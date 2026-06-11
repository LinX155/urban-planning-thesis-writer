"""Artifact-oriented helpers for schema-v2 thesis planning and review cycles.

The v2 artifact model stores not just per-section writing constraints, but also
the argument graph, cross-section dependencies, review-cycle plan context, and
re-plan queue. The goal is to keep long-form writing decisions durable across
sessions instead of relying on chat history alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
BLOCKED_STATUS = "blocked_replan"
VALID_PLAN_PHASES = ("bootstrap", "inventory", "outline", "briefs")
VALID_PHASE_STATUSES = {"pending", "in_progress", "completed", "blocked"}
VALID_REASONING_MODES = {
    "describe",
    "compare",
    "correlate",
    "interpret_cautiously",
    "strategy_translate",
}
VALID_JUDGMENT_STATUSES = {"supported", "open_question", "do_not_write"}


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def state_root(workspace: Path) -> Path:
    return workspace / ".urban-planning-thesis-writer"


def resolve_workspace_path(workspace: Path, raw_path: str | None) -> Path | None:
    text = cleaned_text(raw_path)
    if text is None:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = workspace / path
    return path.resolve()


def load_json(path: Path, default):
    if not path.exists():
        return default
    content = path.read_text(encoding="utf-8-sig").strip()
    if not content:
        return default
    return json.loads(content)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def cleaned_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def unique_keep_order(values: list[Any]) -> list[str]:
    seen = set()
    out: list[str] = []
    for value in values:
        text = cleaned_text(value)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def slugify_section(section: str) -> str:
    ascii_part = re.sub(r"[^A-Za-z0-9]+", "-", section).strip("-").lower()
    digest = hashlib.sha1(section.encode("utf-8")).hexdigest()[:8]
    if ascii_part:
        return f"{ascii_part}-{digest}"
    return f"section-{digest}"


def default_outline() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "main_question": None,
        "sections": [],
        "global_open_questions": [],
        "updated_at": None,
    }


def default_project_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "thesis_title": None,
        "research_object": None,
        "research_scope": None,
        "confirmed_facts_boundary": [],
        "current_markdown": None,
        "research_questions": [],
        "methodological_notes": [],
        "created_at": None,
        "updated_at": None,
    }


def default_brief(section_id: str) -> dict[str, Any]:
    title = section_id
    return {
        "schema_version": SCHEMA_VERSION,
        "section_id": section_id,
        "title": title,
        "parent_id": None,
        "function": None,
        "write_goal": None,
        "core_question": None,
        "target_length": None,
        "status": "planned",
        "sources": [],
        "confirmed_facts": [],
        "forbidden_moves": [],
        "required_figures": [],
        "required_tables": [],
        "required_formulas": [],
        "open_questions": [],
        "style_notes": [],
        "core_judgments": [],
        "dependency_inputs": [],
        "confirmed_outputs": [],
        "section_skeleton": [],
        "transition_in": None,
        "transition_out": None,
        "replan_watchpoints": [],
        "updated_at": None,
    }


def default_replan_queue() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pending": [],
        "resolved": [],
        "updated_at": None,
    }


def default_terminology() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "terms": [],
        "abbreviations": [],
        "variables": [],
        "updated_at": None,
    }


def default_material_inventory() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "current_markdown": None,
        "candidate_markdown": [],
        "sources": [],
        "uncovered_questions": [],
        "deferred_sources": [],
        "coverage_notes": [],
        "updated_at": None,
    }


def default_phase_record() -> dict[str, Any]:
    return {
        "status": "pending",
        "updated_at": None,
        "note": None,
    }


def default_plan_state() -> dict[str, Any]:
    return {
        "current_phase": None,
        "resume_from": None,
        "last_plan_summary": None,
        "current_markdown": None,
        "candidate_markdown": [],
        "target_sections": [],
        "completed_phases": [],
        "material_inventory_path": None,
        "outline_path": None,
        "latest_brief_batch": [],
        "phase_status": {phase: default_phase_record() for phase in VALID_PLAN_PHASES},
        "updated_at": None,
    }


def default_progress() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "completed_sections": [],
        "pending_sections": [],
        "blocked_sections": [],
        "pending_replan_items": [],
        "last_snapshot": None,
        "last_backup": None,
        "last_review_section": None,
        "last_review_summary": None,
        "last_write_context": None,
        "review_rounds": 0,
        "plan_state": default_plan_state(),
    }


def merge_string_lists(existing: list[Any], new_values: list[Any]) -> list[str]:
    return unique_keep_order(list(existing) + list(new_values))


def normalize_plan_phase(value: Any) -> str | None:
    text = cleaned_text(value)
    if text in VALID_PLAN_PHASES:
        return text
    return None


def normalize_phase_status(value: Any) -> str | None:
    text = cleaned_text(value)
    if text in VALID_PHASE_STATUSES:
        return text
    return None


def normalize_project_state(raw: Any) -> dict[str, Any]:
    project = default_project_state()
    if not isinstance(raw, dict):
        return project
    for key in ("thesis_title", "research_object", "research_scope", "current_markdown", "created_at", "updated_at"):
        value = raw.get(key)
        if value is not None:
            project[key] = value
    project["confirmed_facts_boundary"] = unique_keep_order(raw.get("confirmed_facts_boundary", []))
    project["research_questions"] = unique_keep_order(raw.get("research_questions", []))
    project["methodological_notes"] = unique_keep_order(raw.get("methodological_notes", []))
    return project


def normalize_material_source(raw: Any, index: int | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {"path": cleaned_text(raw)}
    source_path = cleaned_text(raw.get("path") or raw.get("file") or raw.get("source_path"))
    title = cleaned_text(raw.get("title")) or (Path(source_path).name if source_path else None)
    identity_seed = cleaned_text(raw.get("source_id")) or source_path or title or f"source-{index or timestamp()}"
    source_id = cleaned_text(raw.get("source_id")) or (
        f"source-{hashlib.sha1(identity_seed.encode('utf-8')).hexdigest()[:10]}"
    )
    suffix = Path(source_path).suffix.lower() if source_path else None
    return {
        "source_id": source_id,
        "path": source_path,
        "title": title or source_id,
        "file_type": cleaned_text(raw.get("file_type")) or suffix,
        "role": cleaned_text(raw.get("role")),
        "status": cleaned_text(raw.get("status")) or "indexed",
        "relevance": cleaned_text(raw.get("relevance")),
        "extracted_claims": unique_keep_order(raw.get("extracted_claims", [])),
        "figure_ids": unique_keep_order(raw.get("figure_ids", [])),
        "table_ids": unique_keep_order(raw.get("table_ids", [])),
        "formula_ids": unique_keep_order(raw.get("formula_ids", [])),
        "open_questions": unique_keep_order(raw.get("open_questions", [])),
        "notes": unique_keep_order(raw.get("notes", [])),
    }


def merge_material_source(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key in ("path", "title", "file_type", "role", "status", "relevance"):
        value = patch.get(key)
        if value is not None:
            merged[key] = value
    for key in ("extracted_claims", "figure_ids", "table_ids", "formula_ids", "open_questions", "notes"):
        merged[key] = merge_string_lists(existing.get(key, []), patch.get(key, []))
    return merged


def normalize_material_inventory(raw: Any) -> dict[str, Any]:
    inventory = default_material_inventory()
    if not isinstance(raw, dict):
        return inventory
    for key in ("current_markdown", "updated_at"):
        value = raw.get(key)
        if value is not None:
            inventory[key] = value
    inventory["candidate_markdown"] = unique_keep_order(raw.get("candidate_markdown", []))
    inventory["uncovered_questions"] = unique_keep_order(raw.get("uncovered_questions", []))
    inventory["deferred_sources"] = unique_keep_order(raw.get("deferred_sources", []))
    inventory["coverage_notes"] = unique_keep_order(raw.get("coverage_notes", []))
    inventory["sources"] = [
        normalize_material_source(item, index)
        for index, item in enumerate(ensure_list(raw.get("sources")), start=1)
    ]
    return inventory


def normalize_plan_state(raw: Any) -> dict[str, Any]:
    plan_state = default_plan_state()
    if not isinstance(raw, dict):
        return plan_state
    plan_state["current_phase"] = normalize_plan_phase(raw.get("current_phase"))
    for key in ("resume_from", "last_plan_summary", "current_markdown", "material_inventory_path", "outline_path", "updated_at"):
        value = raw.get(key)
        if value is not None:
            plan_state[key] = value
    plan_state["candidate_markdown"] = unique_keep_order(raw.get("candidate_markdown", []))
    plan_state["target_sections"] = unique_keep_order(raw.get("target_sections", []))
    plan_state["latest_brief_batch"] = unique_keep_order(raw.get("latest_brief_batch", []))
    plan_state["completed_phases"] = [
        phase for phase in unique_keep_order(raw.get("completed_phases", [])) if phase in VALID_PLAN_PHASES
    ]

    raw_phase_status = raw.get("phase_status", {})
    if isinstance(raw_phase_status, dict):
        for phase in VALID_PLAN_PHASES:
            candidate = raw_phase_status.get(phase)
            if isinstance(candidate, dict):
                status = normalize_phase_status(candidate.get("status"))
                if status is not None:
                    plan_state["phase_status"][phase]["status"] = status
                if "note" in candidate:
                    plan_state["phase_status"][phase]["note"] = cleaned_text(candidate.get("note"))
                if candidate.get("updated_at") is not None:
                    plan_state["phase_status"][phase]["updated_at"] = candidate.get("updated_at")

    completed_from_status = [
        phase for phase in VALID_PLAN_PHASES if plan_state["phase_status"][phase]["status"] == "completed"
    ]
    plan_state["completed_phases"] = merge_string_lists(
        plan_state.get("completed_phases", []),
        completed_from_status,
    )
    return plan_state


def dedupe_dict_items(items: list[dict[str, Any]], identity_fn) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen = set()
    for item in items:
        key = identity_fn(item)
        if key and key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def normalize_outline_section(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        text = cleaned_text(raw)
        raw = {"section_id": text, "title": text}
    section_id = cleaned_text(raw.get("section_id") or raw.get("section") or raw.get("title"))
    if not section_id:
        raise SystemExit("Outline section payload is missing section_id/title.")
    title = cleaned_text(raw.get("title")) or section_id
    level_raw = raw.get("level")
    try:
        level = int(level_raw) if level_raw is not None else None
    except (TypeError, ValueError):
        level = None
    return {
        "section_id": section_id,
        "title": title,
        "level": level,
        "function": cleaned_text(raw.get("function")),
        "depends_on": unique_keep_order(ensure_list(raw.get("depends_on"))),
        "feeds_into": unique_keep_order(ensure_list(raw.get("feeds_into"))),
        "status": cleaned_text(raw.get("status")) or "planned",
    }


def merge_outline_section(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key in ("title", "function", "status"):
        value = patch.get(key)
        if value is not None:
            merged[key] = value
    if patch.get("level") is not None:
        merged["level"] = patch["level"]
    merged["depends_on"] = merge_string_lists(existing.get("depends_on", []), patch.get("depends_on", []))
    merged["feeds_into"] = merge_string_lists(existing.get("feeds_into", []), patch.get("feeds_into", []))
    return merged


def normalize_outline(raw: Any) -> dict[str, Any]:
    outline = default_outline()
    if not isinstance(raw, dict):
        return outline
    main_question = cleaned_text(raw.get("main_question"))
    if main_question is not None:
        outline["main_question"] = main_question
    outline["sections"] = []
    for section in ensure_list(raw.get("sections")):
        try:
            outline["sections"].append(normalize_outline_section(section))
        except SystemExit:
            continue
    outline["global_open_questions"] = unique_keep_order(
        ensure_list(raw.get("global_open_questions") or raw.get("open_questions"))
    )
    outline["updated_at"] = raw.get("updated_at")
    return outline


def load_outline(workspace: Path) -> dict[str, Any]:
    path = state_root(workspace) / "state" / "outline.json"
    return normalize_outline(load_json(path, default_outline()))


def write_outline(workspace: Path, outline: dict[str, Any]) -> Path:
    normalized = normalize_outline(outline)
    normalized["schema_version"] = SCHEMA_VERSION
    normalized["updated_at"] = iso_now()
    path = state_root(workspace) / "state" / "outline.json"
    write_json(path, normalized)
    return path


def load_project_state(workspace: Path) -> dict[str, Any]:
    path = state_root(workspace) / "state" / "project.json"
    return normalize_project_state(load_json(path, default_project_state()))


def write_project_state(workspace: Path, project: dict[str, Any]) -> Path:
    normalized = normalize_project_state(project)
    normalized["schema_version"] = SCHEMA_VERSION
    if not normalized.get("created_at"):
        normalized["created_at"] = iso_now()
    normalized["updated_at"] = iso_now()
    path = state_root(workspace) / "state" / "project.json"
    write_json(path, normalized)
    return path


def load_material_inventory(workspace: Path) -> dict[str, Any]:
    path = state_root(workspace) / "state" / "material_inventory.json"
    return normalize_material_inventory(load_json(path, default_material_inventory()))


def write_material_inventory(workspace: Path, inventory: dict[str, Any]) -> Path:
    normalized = normalize_material_inventory(inventory)
    normalized["schema_version"] = SCHEMA_VERSION
    normalized["updated_at"] = iso_now()
    path = state_root(workspace) / "state" / "material_inventory.json"
    write_json(path, normalized)
    return path


def normalize_terminology(raw: Any) -> dict[str, Any]:
    terminology = default_terminology()
    if not isinstance(raw, dict):
        return terminology
    for key in ("updated_at",):
        value = raw.get(key)
        if value is not None:
            terminology[key] = value
    terminology["terms"] = unique_keep_order(raw.get("terms", []))
    terminology["abbreviations"] = unique_keep_order(raw.get("abbreviations", []))
    terminology["variables"] = unique_keep_order(raw.get("variables", []))
    return terminology


def load_terminology(workspace: Path) -> dict[str, Any]:
    path = state_root(workspace) / "state" / "terminology.json"
    return normalize_terminology(load_json(path, default_terminology()))


def write_terminology(workspace: Path, terminology: dict[str, Any]) -> Path:
    normalized = normalize_terminology(terminology)
    normalized["schema_version"] = SCHEMA_VERSION
    normalized["updated_at"] = iso_now()
    path = state_root(workspace) / "state" / "terminology.json"
    write_json(path, normalized)
    return path


def upsert_terminology(workspace: Path, payload_file: Path) -> dict[str, Any]:
    payload = normalize_terminology(load_json(payload_file, {}))
    existing = load_terminology(workspace)
    merged = dict(existing)
    for key in ("terms", "abbreviations", "variables"):
        merged[key] = merge_string_lists(existing.get(key, []), payload.get(key, []))
    saved = write_terminology(workspace, merged)
    return {
        "terminology": str(saved),
        "terms_count": len(merged.get("terms", [])),
        "abbreviations_count": len(merged.get("abbreviations", [])),
        "variables_count": len(merged.get("variables", [])),
    }


def find_outline_section(outline: dict[str, Any], section_ref: str) -> tuple[int | None, dict[str, Any] | None]:
    wanted = cleaned_text(section_ref)
    if not wanted:
        return None, None
    for index, section in enumerate(outline.get("sections", [])):
        if wanted in {
            cleaned_text(section.get("section_id")),
            cleaned_text(section.get("title")),
        }:
            return index, section
    return None, None


def normalize_judgment(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {"text": cleaned_text(raw)}
    text = cleaned_text(raw.get("text"))
    if not text:
        raise SystemExit("Each core_judgment requires text.")
    judgment_id = cleaned_text(raw.get("judgment_id")) or f"judgment-{index}"
    status = cleaned_text(raw.get("status")) or "supported"
    if status not in VALID_JUDGMENT_STATUSES:
        status = "supported"
    reasoning_mode = cleaned_text(raw.get("reasoning_mode")) or "describe"
    if reasoning_mode not in VALID_REASONING_MODES:
        reasoning_mode = "describe"
    return {
        "judgment_id": judgment_id,
        "text": text,
        "status": status,
        "reasoning_mode": reasoning_mode,
        "evidence_anchors": unique_keep_order(
            ensure_list(raw.get("evidence_anchors") or raw.get("evidence"))
        ),
    }


def normalize_dependency_input(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {"from_section": cleaned_text(raw)}
    from_section = cleaned_text(raw.get("from_section"))
    if not from_section:
        raise SystemExit("Each dependency_input requires from_section.")
    return {
        "dependency_id": cleaned_text(raw.get("dependency_id")) or f"dependency-{index}",
        "from_section": from_section,
        "required_output": cleaned_text(raw.get("required_output")),
        "note": cleaned_text(raw.get("note")),
    }


def normalize_confirmed_output(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {"text": cleaned_text(raw)}
    text = cleaned_text(raw.get("text"))
    if not text:
        raise SystemExit("Each confirmed_output requires text.")
    return {
        "output_id": cleaned_text(raw.get("output_id")) or f"output-{index}",
        "text": text,
        "status": cleaned_text(raw.get("status")) or "confirmed",
    }


def normalize_section_task(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {"title": cleaned_text(raw)}
    title = cleaned_text(raw.get("title") or raw.get("task"))
    if not title:
        raise SystemExit("Each section_skeleton item requires title.")
    return {
        "task_id": cleaned_text(raw.get("task_id")) or f"task-{index}",
        "title": title,
        "serves_judgments": unique_keep_order(ensure_list(raw.get("serves_judgments"))),
        "evidence_anchors": unique_keep_order(
            ensure_list(raw.get("evidence_anchors") or raw.get("required_evidence"))
        ),
    }


def normalize_watchpoint(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {"condition": cleaned_text(raw)}
    condition = cleaned_text(raw.get("condition"))
    if not condition:
        raise SystemExit("Each replan_watchpoint requires condition.")
    return {
        "watch_id": cleaned_text(raw.get("watch_id")) or f"watch-{index}",
        "condition": condition,
        "replan_action": cleaned_text(raw.get("replan_action")) or "return_to_plan",
        "note": cleaned_text(raw.get("note")),
    }


def normalize_brief(raw: Any, fallback_section: str | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    section_id = cleaned_text(
        raw.get("section_id") or raw.get("section") or raw.get("title") or fallback_section
    )
    if not section_id:
        raise SystemExit("Chapter brief requires section_id/title.")
    brief = default_brief(section_id)
    brief["title"] = cleaned_text(raw.get("title") or raw.get("section")) or section_id
    for key in ("parent_id", "function", "write_goal", "core_question", "target_length", "transition_in", "transition_out"):
        value = cleaned_text(raw.get(key))
        if value is not None:
            brief[key] = value
    brief["schema_version"] = SCHEMA_VERSION
    brief["status"] = cleaned_text(raw.get("status")) or "planned"
    brief["sources"] = unique_keep_order(ensure_list(raw.get("sources") or raw.get("source")))
    brief["confirmed_facts"] = unique_keep_order(ensure_list(raw.get("confirmed_facts") or raw.get("fact")))
    brief["forbidden_moves"] = unique_keep_order(ensure_list(raw.get("forbidden_moves") or raw.get("forbidden")))
    brief["required_figures"] = unique_keep_order(
        ensure_list(raw.get("required_figures") or raw.get("required_figure"))
    )
    brief["required_tables"] = unique_keep_order(
        ensure_list(raw.get("required_tables") or raw.get("required_table"))
    )
    brief["required_formulas"] = unique_keep_order(
        ensure_list(raw.get("required_formulas") or raw.get("required_formula"))
    )
    brief["open_questions"] = unique_keep_order(ensure_list(raw.get("open_questions") or raw.get("open_question")))
    brief["style_notes"] = unique_keep_order(ensure_list(raw.get("style_notes") or raw.get("style_note")))
    brief["core_judgments"] = [
        normalize_judgment(item, index)
        for index, item in enumerate(ensure_list(raw.get("core_judgments")), start=1)
        if cleaned_text(item if not isinstance(item, dict) else item.get("text"))
    ]
    brief["dependency_inputs"] = [
        normalize_dependency_input(item, index)
        for index, item in enumerate(ensure_list(raw.get("dependency_inputs")), start=1)
        if cleaned_text(item if not isinstance(item, dict) else item.get("from_section"))
    ]
    brief["confirmed_outputs"] = [
        normalize_confirmed_output(item, index)
        for index, item in enumerate(ensure_list(raw.get("confirmed_outputs")), start=1)
        if cleaned_text(item if not isinstance(item, dict) else item.get("text"))
    ]
    brief["section_skeleton"] = [
        normalize_section_task(item, index)
        for index, item in enumerate(ensure_list(raw.get("section_skeleton")), start=1)
        if cleaned_text(item if not isinstance(item, dict) else item.get("title") or item.get("task"))
    ]
    brief["replan_watchpoints"] = [
        normalize_watchpoint(item, index)
        for index, item in enumerate(ensure_list(raw.get("replan_watchpoints")), start=1)
        if cleaned_text(item if not isinstance(item, dict) else item.get("condition"))
    ]
    brief["updated_at"] = raw.get("updated_at")
    return brief


def merge_dict_list(
    existing: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
    primary_key: str,
    fallback_key: str,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for item in existing + new_items:
        key = cleaned_text(item.get(primary_key)) or cleaned_text(item.get(fallback_key))
        if not key:
            continue
        if key in seen:
            merged[seen[key]] = item
        else:
            seen[key] = len(merged)
            merged.append(item)
    return merged


def merge_brief(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    merged["schema_version"] = SCHEMA_VERSION
    merged["section_id"] = patch["section_id"]
    for key in (
        "title",
        "parent_id",
        "function",
        "write_goal",
        "core_question",
        "target_length",
        "status",
        "transition_in",
        "transition_out",
    ):
        value = patch.get(key)
        if value is not None:
            merged[key] = value
    for key in (
        "sources",
        "confirmed_facts",
        "forbidden_moves",
        "required_figures",
        "required_tables",
        "required_formulas",
        "open_questions",
        "style_notes",
    ):
        merged[key] = merge_string_lists(existing.get(key, []), patch.get(key, []))
    merged["core_judgments"] = merge_dict_list(
        existing.get("core_judgments", []),
        patch.get("core_judgments", []),
        "judgment_id",
        "text",
    )
    merged["dependency_inputs"] = merge_dict_list(
        existing.get("dependency_inputs", []),
        patch.get("dependency_inputs", []),
        "dependency_id",
        "from_section",
    )
    merged["confirmed_outputs"] = merge_dict_list(
        existing.get("confirmed_outputs", []),
        patch.get("confirmed_outputs", []),
        "output_id",
        "text",
    )
    merged["section_skeleton"] = merge_dict_list(
        existing.get("section_skeleton", []),
        patch.get("section_skeleton", []),
        "task_id",
        "title",
    )
    merged["replan_watchpoints"] = merge_dict_list(
        existing.get("replan_watchpoints", []),
        patch.get("replan_watchpoints", []),
        "watch_id",
        "condition",
    )
    merged["updated_at"] = iso_now()
    return merged


def load_all_briefs(workspace: Path) -> list[tuple[Path, dict[str, Any]]]:
    chapters_dir = state_root(workspace) / "state" / "chapters"
    if not chapters_dir.exists():
        return []
    briefs: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(chapters_dir.glob("*.json")):
        try:
            briefs.append((path, normalize_brief(load_json(path, {}))))
        except SystemExit:
            continue
    return briefs


def resolve_brief_path(workspace: Path, section_ref: str) -> Path | None:
    chapters_dir = state_root(workspace) / "state" / "chapters"
    direct = chapters_dir / f"{slugify_section(section_ref)}.json"
    if direct.exists():
        return direct
    wanted = cleaned_text(section_ref)
    if not wanted:
        return None
    for path, brief in load_all_briefs(workspace):
        if wanted in {
            cleaned_text(brief.get("section_id")),
            cleaned_text(brief.get("title")),
        }:
            return path
    return None


def load_brief(workspace: Path, section_ref: str) -> tuple[Path, dict[str, Any]]:
    brief_path = resolve_brief_path(workspace, section_ref)
    if brief_path is None:
        raise SystemExit(f"Could not find chapter brief for '{section_ref}'.")
    return brief_path, normalize_brief(load_json(brief_path, {}), fallback_section=section_ref)


def write_brief(workspace: Path, brief: dict[str, Any]) -> Path:
    chapters_dir = state_root(workspace) / "state" / "chapters"
    brief_path = chapters_dir / f"{slugify_section(brief['section_id'])}.json"
    write_json(brief_path, brief)
    return brief_path


def normalize_replan_item(raw: Any, index: int | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SystemExit("Re-plan item payload must be an object.")
    source_section = cleaned_text(raw.get("source_section") or raw.get("section"))
    if not source_section:
        raise SystemExit("Re-plan item requires source_section.")
    item_id = cleaned_text(raw.get("item_id")) or f"replan-{index or timestamp()}"
    return {
        "item_id": item_id,
        "source_section": source_section,
        "trigger_type": cleaned_text(raw.get("trigger_type")) or "manual_review",
        "reason": cleaned_text(raw.get("reason")) or "No reason provided.",
        "affected_sections": unique_keep_order(ensure_list(raw.get("affected_sections"))),
        "required_action": cleaned_text(raw.get("required_action")) or "return_to_plan",
        "status": cleaned_text(raw.get("status")) or "pending",
        "created_at": raw.get("created_at") or iso_now(),
        "resolved_at": raw.get("resolved_at"),
        "note": cleaned_text(raw.get("note")),
    }


def load_replan_queue(workspace: Path) -> dict[str, Any]:
    path = state_root(workspace) / "state" / "replan_queue.json"
    raw = load_json(path, default_replan_queue())
    queue = default_replan_queue()
    queue["schema_version"] = SCHEMA_VERSION
    queue["pending"] = [
        normalize_replan_item(item, index)
        for index, item in enumerate(ensure_list(raw.get("pending")), start=1)
        if isinstance(item, dict)
    ]
    queue["resolved"] = [
        normalize_replan_item(item, index)
        for index, item in enumerate(ensure_list(raw.get("resolved")), start=1)
        if isinstance(item, dict)
    ]
    queue["updated_at"] = raw.get("updated_at")
    return queue


def write_replan_queue(workspace: Path, queue: dict[str, Any]) -> Path:
    queue["schema_version"] = SCHEMA_VERSION
    queue["updated_at"] = iso_now()
    path = state_root(workspace) / "state" / "replan_queue.json"
    write_json(path, queue)
    return path


def load_progress(workspace: Path) -> dict[str, Any]:
    path = state_root(workspace) / "state" / "progress.json"
    raw = load_json(path, default_progress())
    progress = default_progress()
    progress.update(raw)
    progress["schema_version"] = SCHEMA_VERSION
    progress["completed_sections"] = unique_keep_order(progress.get("completed_sections", []))
    progress["pending_sections"] = unique_keep_order(progress.get("pending_sections", []))
    progress["blocked_sections"] = unique_keep_order(progress.get("blocked_sections", []))
    progress["pending_replan_items"] = unique_keep_order(progress.get("pending_replan_items", []))
    progress["plan_state"] = normalize_plan_state(progress.get("plan_state"))
    return progress


def write_progress(workspace: Path, progress: dict[str, Any]) -> Path:
    progress["schema_version"] = SCHEMA_VERSION
    progress["plan_state"] = normalize_plan_state(progress.get("plan_state"))
    path = state_root(workspace) / "state" / "progress.json"
    write_json(path, progress)
    return path


def apply_blocked_sections(workspace: Path, queue: dict[str, Any]) -> None:
    outline = load_outline(workspace)
    blocked_sections = set()
    for item in queue.get("pending", []):
        blocked_sections.update(item.get("affected_sections", []))

    for blocked in blocked_sections:
        _, section = find_outline_section(outline, blocked)
        if section is not None:
            section["status"] = BLOCKED_STATUS
        brief_path = resolve_brief_path(workspace, blocked)
        if brief_path is not None:
            brief = normalize_brief(load_json(brief_path, {}), fallback_section=blocked)
            brief["status"] = BLOCKED_STATUS
            brief["updated_at"] = iso_now()
            write_json(brief_path, brief)

    for section in outline.get("sections", []):
        if section["section_id"] not in blocked_sections and section.get("status") == BLOCKED_STATUS:
            section["status"] = "planned"
    outline["updated_at"] = iso_now()
    write_outline(workspace, outline)

    progress = load_progress(workspace)
    progress["blocked_sections"] = sorted(blocked_sections)
    progress["pending_replan_items"] = sorted(item["item_id"] for item in queue.get("pending", []))
    write_progress(workspace, progress)


def collect_replan_blockers(queue: dict[str, Any], section_id: str, dependency_sections: list[str]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    wanted = {section_id, *dependency_sections}
    for item in queue.get("pending", []):
        affected = set(item.get("affected_sections", []))
        if item.get("source_section") == section_id or wanted.intersection(affected):
            blockers.append(item)
    return blockers


def read_latest_review_memory(workspace: Path, section_id: str) -> dict[str, Any]:
    root = state_root(workspace) / "state" / "memory"
    global_memory = load_json(root / "user_revision_preferences.json", {})
    section_memory = load_json(root / "section_memory.json", {})
    return {
        "global_preferences": global_memory,
        "section_memory": section_memory.get("sections", {}).get(section_id, {}),
    }


def upsert_project_state(
    workspace: Path,
    thesis_title: str | None,
    research_object: str | None,
    research_scope: str | None,
    current_markdown: str | None,
    confirmed_facts: list[str],
    research_questions: list[str],
    methodological_notes: list[str],
    payload_file: Path | None,
) -> dict[str, Any]:
    existing = load_project_state(workspace)
    if payload_file is not None:
        payload = normalize_project_state(load_json(payload_file, {}))
    else:
        payload = normalize_project_state(
            {
                "thesis_title": thesis_title,
                "research_object": research_object,
                "research_scope": research_scope,
                "current_markdown": current_markdown,
                "confirmed_facts_boundary": confirmed_facts,
                "research_questions": research_questions,
                "methodological_notes": methodological_notes,
            }
        )

    merged = dict(existing)
    for key in ("thesis_title", "research_object", "research_scope", "current_markdown"):
        value = payload.get(key)
        if value is not None:
            merged[key] = value
    merged["confirmed_facts_boundary"] = merge_string_lists(
        existing.get("confirmed_facts_boundary", []),
        payload.get("confirmed_facts_boundary", []),
    )
    merged["research_questions"] = merge_string_lists(
        existing.get("research_questions", []),
        payload.get("research_questions", []),
    )
    merged["methodological_notes"] = merge_string_lists(
        existing.get("methodological_notes", []),
        payload.get("methodological_notes", []),
    )
    saved = write_project_state(workspace, merged)
    return {"project": str(saved), "current_markdown": merged.get("current_markdown")}


def upsert_material_inventory(workspace: Path, payload_file: Path) -> dict[str, Any]:
    payload = normalize_material_inventory(load_json(payload_file, {}))
    existing = load_material_inventory(workspace)
    merged = dict(existing)
    if payload.get("current_markdown") is not None:
        merged["current_markdown"] = payload["current_markdown"]
    for key in ("candidate_markdown", "uncovered_questions", "deferred_sources", "coverage_notes"):
        merged[key] = merge_string_lists(existing.get(key, []), payload.get(key, []))

    sources_by_id = {item["source_id"]: item for item in existing.get("sources", [])}
    for item in payload.get("sources", []):
        source_id = item["source_id"]
        if source_id in sources_by_id:
            sources_by_id[source_id] = merge_material_source(sources_by_id[source_id], item)
        else:
            sources_by_id[source_id] = item
    merged["sources"] = list(sources_by_id.values())

    saved = write_material_inventory(workspace, merged)
    return {
        "material_inventory": str(saved),
        "current_markdown": merged.get("current_markdown"),
        "sources_upserted": [item["source_id"] for item in payload.get("sources", [])],
    }


def update_plan_progress(
    workspace: Path,
    phase: str | None,
    status: str | None,
    note: str | None,
    current_markdown: str | None,
    candidate_markdown: list[str],
    target_sections: list[str],
    resume_from: str | None,
    material_inventory_path: str | None,
    outline_path: str | None,
    latest_brief_batch: list[str],
    summary: str | None,
    payload_file: Path | None,
) -> dict[str, Any]:
    progress = load_progress(workspace)
    plan_state = normalize_plan_state(progress.get("plan_state"))

    if payload_file is not None:
        patch = load_json(payload_file, {})
        if not isinstance(patch, dict):
            raise SystemExit("update-plan-progress payload must be an object.")
    else:
        patch = {}

    normalized_phase = normalize_plan_phase(phase or patch.get("current_phase") or patch.get("phase"))
    normalized_status = normalize_phase_status(status)

    if normalized_phase is not None:
        plan_state["current_phase"] = normalized_phase
        if normalized_status is not None:
            plan_state["phase_status"][normalized_phase]["status"] = normalized_status
        if note is not None:
            plan_state["phase_status"][normalized_phase]["note"] = cleaned_text(note)
        if normalized_status is not None or note is not None:
            plan_state["phase_status"][normalized_phase]["updated_at"] = iso_now()

    raw_phase_status = patch.get("phase_status", {})
    if isinstance(raw_phase_status, dict):
        for candidate_phase, candidate_payload in raw_phase_status.items():
            phase_name = normalize_plan_phase(candidate_phase)
            if phase_name is None or not isinstance(candidate_payload, dict):
                continue
            candidate_status = normalize_phase_status(candidate_payload.get("status"))
            if candidate_status is not None:
                plan_state["phase_status"][phase_name]["status"] = candidate_status
            if "note" in candidate_payload:
                plan_state["phase_status"][phase_name]["note"] = cleaned_text(candidate_payload.get("note"))
            plan_state["phase_status"][phase_name]["updated_at"] = candidate_payload.get("updated_at") or iso_now()

    if patch.get("current_phase") is not None:
        plan_state["current_phase"] = normalize_plan_phase(patch.get("current_phase"))
    if patch.get("resume_from") is not None:
        plan_state["resume_from"] = patch.get("resume_from")
    if patch.get("last_plan_summary") is not None:
        plan_state["last_plan_summary"] = patch.get("last_plan_summary")
    if patch.get("current_markdown") is not None:
        plan_state["current_markdown"] = patch.get("current_markdown")
    if patch.get("material_inventory_path") is not None:
        plan_state["material_inventory_path"] = patch.get("material_inventory_path")
    if patch.get("outline_path") is not None:
        plan_state["outline_path"] = patch.get("outline_path")

    if current_markdown is not None:
        plan_state["current_markdown"] = current_markdown
    if resume_from is not None:
        plan_state["resume_from"] = resume_from
    if material_inventory_path is not None:
        plan_state["material_inventory_path"] = material_inventory_path
    if outline_path is not None:
        plan_state["outline_path"] = outline_path
    if summary is not None:
        plan_state["last_plan_summary"] = summary

    plan_state["candidate_markdown"] = merge_string_lists(
        plan_state.get("candidate_markdown", []),
        [*ensure_list(patch.get("candidate_markdown")), *candidate_markdown],
    )
    plan_state["target_sections"] = merge_string_lists(
        plan_state.get("target_sections", []),
        [*ensure_list(patch.get("target_sections")), *target_sections],
    )
    plan_state["latest_brief_batch"] = merge_string_lists(
        plan_state.get("latest_brief_batch", []),
        [*ensure_list(patch.get("latest_brief_batch")), *latest_brief_batch],
    )
    completed = [
        phase_name
        for phase_name in VALID_PLAN_PHASES
        if plan_state["phase_status"][phase_name]["status"] == "completed"
    ]
    plan_state["completed_phases"] = merge_string_lists(
        ensure_list(patch.get("completed_phases")) or plan_state.get("completed_phases", []),
        completed,
    )
    plan_state["updated_at"] = iso_now()

    progress["plan_state"] = plan_state
    path = write_progress(workspace, progress)
    return {
        "progress": str(path),
        "current_phase": plan_state.get("current_phase"),
        "completed_phases": plan_state.get("completed_phases", []),
    }


def upsert_outline_section(workspace: Path, payload_file: Path) -> dict[str, Any]:
    payload = load_json(payload_file, {})
    outline = load_outline(workspace)

    main_question = cleaned_text(payload.get("main_question"))
    if main_question is not None:
        outline["main_question"] = main_question
    outline["global_open_questions"] = merge_string_lists(
        outline.get("global_open_questions", []),
        ensure_list(payload.get("global_open_questions")),
    )

    raw_sections = ensure_list(payload.get("sections"))
    if not raw_sections and payload.get("section"):
        raw_sections = ensure_list(payload.get("section"))
    if not raw_sections and (
        payload.get("section_id") or payload.get("title") or payload.get("section")
    ):
        raw_sections = [payload]

    inserted: list[str] = []
    for raw_section in raw_sections:
        normalized = normalize_outline_section(raw_section)
        index, existing = find_outline_section(outline, normalized["section_id"])
        if existing is None or index is None:
            outline["sections"].append(normalized)
        else:
            outline["sections"][index] = merge_outline_section(existing, normalized)
        inserted.append(normalized["section_id"])

    write_outline(workspace, outline)
    return {
        "outline": str(state_root(workspace) / "state" / "outline.json"),
        "main_question": outline.get("main_question"),
        "sections_upserted": inserted,
    }


def upsert_chapter_brief(
    workspace: Path,
    section: str | None,
    write_goal: str | None,
    target_length: str | None,
    status: str,
    sources: list[str],
    facts: list[str],
    forbidden: list[str],
    required_figures: list[str],
    required_tables: list[str],
    required_formulas: list[str],
    open_questions: list[str],
    style_notes: list[str],
    payload_file: Path | None,
) -> dict:
    if payload_file is not None:
        payload = normalize_brief(load_json(payload_file, {}), fallback_section=section)
    else:
        if not section:
            raise SystemExit("upsert-chapter-brief requires --section when no payload-file is given.")
        payload = normalize_brief(
            {
                "section_id": section,
                "title": section,
                "write_goal": write_goal,
                "target_length": target_length,
                "status": status,
                "sources": sources,
                "confirmed_facts": facts,
                "forbidden_moves": forbidden,
                "required_figures": required_figures,
                "required_tables": required_tables,
                "required_formulas": required_formulas,
                "open_questions": open_questions,
                "style_notes": style_notes,
            },
            fallback_section=section,
        )

    section_id = payload["section_id"]
    brief_path = resolve_brief_path(workspace, section_id)
    existing = normalize_brief(load_json(brief_path, {}), fallback_section=section_id) if brief_path else default_brief(section_id)
    merged = merge_brief(existing, payload)
    saved_path = write_brief(workspace, merged)
    return {"brief": str(saved_path), "section_id": section_id, "status": merged["status"]}


def build_write_context(workspace: Path, section: str, output_path: Path | None = None) -> dict[str, Any]:
    if output_path is None:
        output_path = state_root(workspace) / "state" / "current_write_context.json"
    _, brief = load_brief(workspace, section)
    outline = load_outline(workspace)
    queue = load_replan_queue(workspace)
    _, outline_section = find_outline_section(outline, brief["section_id"])
    outline_section = outline_section or normalize_outline_section(
        {
            "section_id": brief["section_id"],
            "title": brief["title"],
            "status": brief["status"],
        }
    )

    dependency_sections = unique_keep_order(
        [*outline_section.get("depends_on", []), *[item["from_section"] for item in brief.get("dependency_inputs", [])]]
    )
    upstream_outputs: list[dict[str, Any]] = []
    unresolved_dependencies: list[dict[str, Any]] = []
    for dependency in brief.get("dependency_inputs", []):
        dep_section = dependency["from_section"]
        try:
            _, dep_brief = load_brief(workspace, dep_section)
        except SystemExit:
            unresolved_dependencies.append(
                {
                    "from_section": dep_section,
                    "required_output": dependency.get("required_output"),
                    "reason": "missing_section_brief",
                }
            )
            continue
        outputs = dep_brief.get("confirmed_outputs", [])
        if not outputs:
            unresolved_dependencies.append(
                {
                    "from_section": dep_section,
                    "required_output": dependency.get("required_output"),
                    "reason": "missing_confirmed_outputs",
                }
            )
            continue
        matched = outputs
        required_output = cleaned_text(dependency.get("required_output"))
        if required_output:
            matched = [
                output
                for output in outputs
                if required_output in {
                    cleaned_text(output.get("output_id")),
                    cleaned_text(output.get("text")),
                }
            ]
            if not matched:
                unresolved_dependencies.append(
                    {
                        "from_section": dep_section,
                        "required_output": required_output,
                        "reason": "required_output_not_confirmed",
                    }
                )
                continue
        for output in matched:
            upstream_outputs.append(
                {
                    "from_section": dep_section,
                    "output_id": output.get("output_id"),
                    "text": output.get("text"),
                    "status": output.get("status"),
                }
            )

    terminology = load_terminology(workspace)
    blocking_replan_items = collect_replan_blockers(queue, brief["section_id"], dependency_sections)
    latest_review_memory = read_latest_review_memory(workspace, brief["section_id"])
    required_evidence = {
        "figures": brief.get("required_figures", []),
        "tables": brief.get("required_tables", []),
        "formulas": brief.get("required_formulas", []),
        "anchors": unique_keep_order(
            anchor
            for judgment in brief.get("core_judgments", [])
            for anchor in judgment.get("evidence_anchors", [])
        ),
    }
    reasoning_mode = unique_keep_order(
        judgment.get("reasoning_mode") for judgment in brief.get("core_judgments", [])
    )
    open_questions = merge_string_lists(
        outline.get("global_open_questions", []),
        brief.get("open_questions", []),
    )

    can_write = not blocking_replan_items and not unresolved_dependencies
    stop_reason = None
    if blocking_replan_items:
        stop_reason = "blocking_replan_items"
    elif unresolved_dependencies:
        stop_reason = "unresolved_dependencies"

    context = {
        "schema_version": SCHEMA_VERSION,
        "section": brief["title"],
        "section_id": brief["section_id"],
        "title": brief["title"],
        "function": brief.get("function"),
        "write_goal": brief.get("write_goal"),
        "core_question": brief.get("core_question"),
        "target_length": brief.get("target_length"),
        "sources": brief.get("sources", []),
        "core_judgments": brief.get("core_judgments", []),
        "reasoning_mode": reasoning_mode,
        "dependency_inputs": brief.get("dependency_inputs", []),
        "upstream_outputs": upstream_outputs,
        "confirmed_facts": brief.get("confirmed_facts", []),
        "forbidden_moves": brief.get("forbidden_moves", []),
        "required_evidence": required_evidence,
        "open_questions": open_questions,
        "replan_watchpoints": brief.get("replan_watchpoints", []),
        "section_skeleton": brief.get("section_skeleton", []),
        "transition_in": brief.get("transition_in"),
        "transition_out": brief.get("transition_out"),
        "confirmed_outputs": brief.get("confirmed_outputs", []),
        "outline_section": outline_section,
        "latest_review_memory": latest_review_memory,
        "terminology": terminology,
        "blocking_replan_items": blocking_replan_items,
        "unresolved_dependencies": unresolved_dependencies,
        "can_write": can_write,
        "stop_reason": stop_reason,
        "updated_at": iso_now(),
    }
    write_json(output_path, context)
    progress = load_progress(workspace)
    progress["last_write_context"] = str(output_path)
    write_progress(workspace, progress)
    return {"context": str(output_path), "section_id": brief["section_id"], "can_write": can_write}


def extract_plan_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_id": context.get("section_id"),
        "title": context.get("title"),
        "write_goal": context.get("write_goal"),
        "target_length": context.get("target_length"),
        "core_question": context.get("core_question"),
        "core_judgments": context.get("core_judgments", []),
        "reasoning_mode": context.get("reasoning_mode", []),
        "dependency_inputs": context.get("dependency_inputs", []),
        "confirmed_facts": context.get("confirmed_facts", []),
        "forbidden_moves": context.get("forbidden_moves", []),
        "required_evidence": context.get("required_evidence", {}),
        "open_questions": context.get("open_questions", []),
        "replan_watchpoints": context.get("replan_watchpoints", []),
        "section_skeleton": context.get("section_skeleton", []),
        "transition_in": context.get("transition_in"),
        "transition_out": context.get("transition_out"),
        "upstream_outputs": context.get("upstream_outputs", []),
    }


def start_review_cycle(
    workspace: Path,
    section: str | None,
    goal: str | None,
    markdown_path: str | None,
    allowed_scope: str | None,
    target_length: str | None,
    sources: list[str],
    constraints: list[str],
    notes: list[str],
    context_file: Path | None,
) -> dict:
    context = load_json(context_file, {}) if context_file is not None else {}
    if context and not context.get("can_write", True):
        raise SystemExit(
            f"Section '{context.get('section_id')}' is blocked. Return to /UPTW-plan before starting a review cycle."
        )
    section_name = cleaned_text(section) or cleaned_text(context.get("section_id") or context.get("section"))
    if not section_name:
        raise SystemExit("start-review-cycle requires --section or a context-file with section_id.")

    cycle_root = state_root(workspace) / "state" / "review-cycles"
    cycle_dir = cycle_root / f"{timestamp()}-{slugify_section(section_name)}"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    plan_context = extract_plan_context(context) if context else {}
    request = {
        "section": section_name,
        "goal": cleaned_text(goal) or plan_context.get("write_goal"),
        "markdown": markdown_path,
        "allowed_scope": cleaned_text(allowed_scope) or cleaned_text(context.get("title")),
        "target_length": cleaned_text(target_length) or plan_context.get("target_length"),
        "sources": merge_string_lists(sources, context.get("sources", [])),
        "constraints": merge_string_lists(constraints, plan_context.get("forbidden_moves", [])),
        "notes": unique_keep_order(notes),
        "plan_context": plan_context,
        "created_at": iso_now(),
    }
    completion = {
        "section": section_name,
        "status": "open",
        "snapshot": None,
        "backup": None,
        "memory_summary": None,
        "output_markdown": None,
        "closed_at": None,
        "notes": [],
        "plan_validation": {
            "judgments_covered": [],
            "required_evidence_used": [],
            "forbidden_moves_clear": None,
            "open_questions_preserved": None,
            "new_replan_item_ids": [],
        },
        "memory_decision": {
            "stable_preferences": [],
            "tentative_observations": [],
            "rejected_generalizations": [],
            "facts_confirmed": [],
            "open_questions": [],
        },
    }

    write_json(cycle_dir / "request.json", request)
    write_json(cycle_dir / "completion.json", completion)
    if context_file is not None and context_file.exists():
        shutil.copy2(context_file, cycle_dir / "context.json")
    return {
        "cycle_dir": str(cycle_dir),
        "request": str(cycle_dir / "request.json"),
        "completion": str(cycle_dir / "completion.json"),
    }


def load_plan_validation(
    plan_validation_file: Path | None,
    judgments_covered: list[str],
    required_evidence_used: list[str],
    forbidden_moves_clear: str | None,
    open_questions_preserved: str | None,
    new_replan_item_ids: list[str],
) -> dict[str, Any]:
    payload = load_json(plan_validation_file, {}) if plan_validation_file else {}
    return {
        "judgments_covered": merge_string_lists(payload.get("judgments_covered", []), judgments_covered),
        "required_evidence_used": merge_string_lists(
            payload.get("required_evidence_used", []), required_evidence_used
        ),
        "forbidden_moves_clear": (
            payload.get("forbidden_moves_clear")
            if "forbidden_moves_clear" in payload
            else None
            if forbidden_moves_clear is None
            else forbidden_moves_clear.lower() == "true"
        ),
        "open_questions_preserved": (
            payload.get("open_questions_preserved")
            if "open_questions_preserved" in payload
            else None
            if open_questions_preserved is None
            else open_questions_preserved.lower() == "true"
        ),
        "new_replan_item_ids": merge_string_lists(
            payload.get("new_replan_item_ids", []), new_replan_item_ids
        ),
    }


def complete_review_cycle(
    workspace: Path,
    cycle_dir: Path,
    status: str,
    snapshot: str | None,
    backup: str | None,
    memory_summary: str | None,
    output_markdown: str | None,
    notes: list[str],
    plan_validation_file: Path | None,
    judgments_covered: list[str],
    required_evidence_used: list[str],
    forbidden_moves_clear: str | None,
    open_questions_preserved: str | None,
    new_replan_item_ids: list[str],
    confirmed_outputs: list[str],
    section_status: str | None,
) -> dict:
    completion_path = cycle_dir / "completion.json"
    completion = load_json(
        completion_path,
        {
            "section": None,
            "status": "open",
            "snapshot": None,
            "backup": None,
            "memory_summary": None,
            "output_markdown": None,
            "closed_at": None,
            "notes": [],
            "plan_validation": {},
        },
    )
    completion["status"] = status
    if snapshot:
        completion["snapshot"] = snapshot
    if backup:
        completion["backup"] = backup
    if memory_summary:
        completion["memory_summary"] = memory_summary
    if output_markdown:
        completion["output_markdown"] = output_markdown
    completion["notes"] = unique_keep_order(list(completion.get("notes", [])) + notes)
    completion["plan_validation"] = load_plan_validation(
        plan_validation_file,
        judgments_covered,
        required_evidence_used,
        forbidden_moves_clear,
        open_questions_preserved,
        new_replan_item_ids,
    )
    completion["closed_at"] = iso_now()
    write_json(completion_path, completion)

    request = load_json(cycle_dir / "request.json", {})
    section_id = cleaned_text(request.get("section"))
    if section_id:
        try:
            brief_path, brief = load_brief(workspace, section_id)
        except SystemExit:
            brief_path = None
            brief = None
        if brief_path is not None and brief is not None:
            if confirmed_outputs:
                brief["confirmed_outputs"] = merge_dict_list(
                    brief.get("confirmed_outputs", []),
                    [normalize_confirmed_output(item, index) for index, item in enumerate(confirmed_outputs, start=1)],
                    "output_id",
                    "text",
                )
            if section_status is not None:
                brief["status"] = section_status
            elif status == "reviewed":
                brief["status"] = "reviewed"
            brief["updated_at"] = iso_now()
            write_json(brief_path, brief)

            outline = load_outline(workspace)
            index, outline_section = find_outline_section(outline, brief["section_id"])
            if index is not None and outline_section is not None:
                outline["sections"][index]["status"] = brief["status"]
                write_outline(workspace, outline)

    return {"completion": str(completion_path), "status": status}


def queue_replan(
    workspace: Path,
    payload_file: Path | None,
    source_section: str | None,
    trigger_type: str | None,
    reason: str | None,
    affected_sections: list[str],
    required_action: str | None,
    note: str | None,
) -> dict[str, Any]:
    if payload_file is not None:
        payload = load_json(payload_file, {})
    else:
        payload = {
            "source_section": source_section,
            "trigger_type": trigger_type,
            "reason": reason,
            "affected_sections": affected_sections,
            "required_action": required_action,
            "note": note,
        }
    queue = load_replan_queue(workspace)
    item = normalize_replan_item(payload, len(queue.get("pending", [])) + len(queue.get("resolved", [])) + 1)
    pending = [existing for existing in queue.get("pending", []) if existing.get("item_id") != item["item_id"]]
    pending.append(item)
    queue["pending"] = pending
    write_replan_queue(workspace, queue)
    apply_blocked_sections(workspace, queue)
    return {"queue": str(state_root(workspace) / "state" / "replan_queue.json"), "item": item}


def resolve_replan(
    workspace: Path,
    item_id: str,
    resolution_status: str,
    note: str | None,
) -> dict[str, Any]:
    queue = load_replan_queue(workspace)
    item = None
    remaining = []
    for existing in queue.get("pending", []):
        if existing.get("item_id") == item_id:
            item = dict(existing)
        else:
            remaining.append(existing)
    if item is None:
        raise SystemExit(f"Could not find pending re-plan item '{item_id}'.")
    item["status"] = resolution_status
    item["resolved_at"] = iso_now()
    if note is not None:
        item["note"] = note
    queue["pending"] = remaining
    queue["resolved"] = [*queue.get("resolved", []), item]
    write_replan_queue(workspace, queue)
    apply_blocked_sections(workspace, queue)
    return {"queue": str(state_root(workspace) / "state" / "replan_queue.json"), "item": item}


def latest_cycle(workspace: Path, section: str | None) -> dict:
    cycle_root = state_root(workspace) / "state" / "review-cycles"
    if not cycle_root.exists():
        return {"cycle_dir": None}
    candidates = [item for item in cycle_root.iterdir() if item.is_dir()]
    if section:
        suffix = slugify_section(section)
        candidates = [item for item in candidates if item.name.endswith(suffix)]
    candidates.sort(key=lambda item: item.name, reverse=True)
    if not candidates:
        return {"cycle_dir": None}
    cycle_dir = candidates[0]
    response = {
        "cycle_dir": str(cycle_dir),
        "request": load_json(cycle_dir / "request.json", {}),
        "completion": load_json(cycle_dir / "completion.json", {}),
    }
    context_path = cycle_dir / "context.json"
    if context_path.exists():
        response["context"] = load_json(context_path, {})
    return response


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_project = sub.add_parser("upsert-project-state")
    p_project.add_argument("--workspace", required=True)
    p_project.add_argument("--thesis-title")
    p_project.add_argument("--research-object")
    p_project.add_argument("--research-scope")
    p_project.add_argument("--current-markdown")
    p_project.add_argument("--fact", action="append", default=[])
    p_project.add_argument("--question", action="append", default=[])
    p_project.add_argument("--method-note", action="append", default=[])
    p_project.add_argument("--payload-file")

    p_inventory = sub.add_parser("upsert-material-inventory")
    p_inventory.add_argument("--workspace", required=True)
    p_inventory.add_argument("--payload-file", required=True)

    p_plan_progress = sub.add_parser("update-plan-progress")
    p_plan_progress.add_argument("--workspace", required=True)
    p_plan_progress.add_argument("--phase")
    p_plan_progress.add_argument("--status")
    p_plan_progress.add_argument("--note")
    p_plan_progress.add_argument("--current-markdown")
    p_plan_progress.add_argument("--candidate-markdown", action="append", default=[])
    p_plan_progress.add_argument("--target-section", action="append", default=[])
    p_plan_progress.add_argument("--resume-from")
    p_plan_progress.add_argument("--material-inventory")
    p_plan_progress.add_argument("--outline-path")
    p_plan_progress.add_argument("--brief-section", action="append", default=[])
    p_plan_progress.add_argument("--summary")
    p_plan_progress.add_argument("--payload-file")

    p_outline = sub.add_parser("upsert-outline-section")
    p_outline.add_argument("--workspace", required=True)
    p_outline.add_argument("--payload-file", required=True)

    p_brief = sub.add_parser("upsert-chapter-brief")
    p_brief.add_argument("--workspace", required=True)
    p_brief.add_argument("--section")
    p_brief.add_argument("--write-goal")
    p_brief.add_argument("--target-length")
    p_brief.add_argument("--status", default="planned")
    p_brief.add_argument("--source", action="append", default=[])
    p_brief.add_argument("--fact", action="append", default=[])
    p_brief.add_argument("--forbidden", action="append", default=[])
    p_brief.add_argument("--required-figure", action="append", default=[])
    p_brief.add_argument("--required-table", action="append", default=[])
    p_brief.add_argument("--required-formula", action="append", default=[])
    p_brief.add_argument("--open-question", action="append", default=[])
    p_brief.add_argument("--style-note", action="append", default=[])
    p_brief.add_argument("--payload-file")

    p_terminology = sub.add_parser("upsert-terminology")
    p_terminology.add_argument("--workspace", required=True)
    p_terminology.add_argument("--payload-file", required=True)

    p_context = sub.add_parser("build-write-context")
    p_context.add_argument("--workspace", required=True)
    p_context.add_argument("--section", required=True)
    p_context.add_argument("--output")

    p_start = sub.add_parser("start-review-cycle")
    p_start.add_argument("--workspace", required=True)
    p_start.add_argument("--section")
    p_start.add_argument("--goal")
    p_start.add_argument("--markdown")
    p_start.add_argument("--allowed-scope")
    p_start.add_argument("--target-length")
    p_start.add_argument("--source", action="append", default=[])
    p_start.add_argument("--constraint", action="append", default=[])
    p_start.add_argument("--note", action="append", default=[])
    p_start.add_argument("--context-file")

    p_complete = sub.add_parser("complete-review-cycle")
    p_complete.add_argument("--workspace", required=True)
    p_complete.add_argument("--cycle-dir", required=True)
    p_complete.add_argument("--status", default="reviewed")
    p_complete.add_argument("--snapshot")
    p_complete.add_argument("--backup")
    p_complete.add_argument("--memory-summary")
    p_complete.add_argument("--output-markdown")
    p_complete.add_argument("--note", action="append", default=[])
    p_complete.add_argument("--plan-validation-file")
    p_complete.add_argument("--covered-judgment", action="append", default=[])
    p_complete.add_argument("--used-evidence", action="append", default=[])
    p_complete.add_argument("--forbidden-moves-clear")
    p_complete.add_argument("--open-questions-preserved")
    p_complete.add_argument("--new-replan-item", action="append", default=[])
    p_complete.add_argument("--confirmed-output", action="append", default=[])
    p_complete.add_argument("--section-status")

    p_queue = sub.add_parser("queue-replan")
    p_queue.add_argument("--workspace", required=True)
    p_queue.add_argument("--payload-file")
    p_queue.add_argument("--source-section")
    p_queue.add_argument("--trigger-type")
    p_queue.add_argument("--reason")
    p_queue.add_argument("--affected-section", action="append", default=[])
    p_queue.add_argument("--required-action")
    p_queue.add_argument("--note")

    p_resolve = sub.add_parser("resolve-replan")
    p_resolve.add_argument("--workspace", required=True)
    p_resolve.add_argument("--item-id", required=True)
    p_resolve.add_argument("--status", default="resolved")
    p_resolve.add_argument("--note")

    p_latest = sub.add_parser("latest-cycle")
    p_latest.add_argument("--workspace", required=True)
    p_latest.add_argument("--section")

    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    if args.command == "upsert-project-state":
        payload = upsert_project_state(
            workspace=workspace,
            thesis_title=args.thesis_title,
            research_object=args.research_object,
            research_scope=args.research_scope,
            current_markdown=str(resolve_workspace_path(workspace, args.current_markdown)) if args.current_markdown else None,
            confirmed_facts=args.fact,
            research_questions=args.question,
            methodological_notes=args.method_note,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
        )
    elif args.command == "upsert-material-inventory":
        payload = upsert_material_inventory(
            workspace=workspace,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
        )
    elif args.command == "update-plan-progress":
        payload = update_plan_progress(
            workspace=workspace,
            phase=args.phase,
            status=args.status,
            note=args.note,
            current_markdown=str(resolve_workspace_path(workspace, args.current_markdown)) if args.current_markdown else None,
            candidate_markdown=[
                str(resolve_workspace_path(workspace, item)) if resolve_workspace_path(workspace, item) is not None else item
                for item in args.candidate_markdown
            ],
            target_sections=args.target_section,
            resume_from=args.resume_from,
            material_inventory_path=(
                str(resolve_workspace_path(workspace, args.material_inventory))
                if args.material_inventory
                else None
            ),
            outline_path=str(resolve_workspace_path(workspace, args.outline_path)) if args.outline_path else None,
            latest_brief_batch=args.brief_section,
            summary=args.summary,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
        )
    elif args.command == "upsert-outline-section":
        payload = upsert_outline_section(
            workspace=workspace,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
        )
    elif args.command == "upsert-chapter-brief":
        payload = upsert_chapter_brief(
            workspace=workspace,
            section=args.section,
            write_goal=args.write_goal,
            target_length=args.target_length,
            status=args.status,
            sources=args.source,
            facts=args.fact,
            forbidden=args.forbidden,
            required_figures=args.required_figure,
            required_tables=args.required_table,
            required_formulas=args.required_formula,
            open_questions=args.open_question,
            style_notes=args.style_note,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
        )
    elif args.command == "upsert-terminology":
        payload = upsert_terminology(
            workspace=workspace,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
        )
    elif args.command == "build-write-context":
        payload = build_write_context(
            workspace=workspace,
            section=args.section,
            output_path=resolve_workspace_path(workspace, args.output) if args.output else None,
        )
    elif args.command == "start-review-cycle":
        payload = start_review_cycle(
            workspace=workspace,
            section=args.section,
            goal=args.goal,
            markdown_path=args.markdown,
            allowed_scope=args.allowed_scope,
            target_length=args.target_length,
            sources=args.source,
            constraints=args.constraint,
            notes=args.note,
            context_file=resolve_workspace_path(workspace, args.context_file),
        )
    elif args.command == "complete-review-cycle":
        payload = complete_review_cycle(
            workspace=workspace,
            cycle_dir=resolve_workspace_path(workspace, args.cycle_dir),
            status=args.status,
            snapshot=str(resolve_workspace_path(workspace, args.snapshot)) if args.snapshot else None,
            backup=str(resolve_workspace_path(workspace, args.backup)) if args.backup else None,
            memory_summary=str(resolve_workspace_path(workspace, args.memory_summary)) if args.memory_summary else None,
            output_markdown=str(resolve_workspace_path(workspace, args.output_markdown)) if args.output_markdown else None,
            notes=args.note,
            plan_validation_file=resolve_workspace_path(workspace, args.plan_validation_file),
            judgments_covered=args.covered_judgment,
            required_evidence_used=args.used_evidence,
            forbidden_moves_clear=args.forbidden_moves_clear,
            open_questions_preserved=args.open_questions_preserved,
            new_replan_item_ids=args.new_replan_item,
            confirmed_outputs=args.confirmed_output,
            section_status=args.section_status,
        )
    elif args.command == "queue-replan":
        payload = queue_replan(
            workspace=workspace,
            payload_file=resolve_workspace_path(workspace, args.payload_file),
            source_section=args.source_section,
            trigger_type=args.trigger_type,
            reason=args.reason,
            affected_sections=args.affected_section,
            required_action=args.required_action,
            note=args.note,
        )
    elif args.command == "resolve-replan":
        payload = resolve_replan(
            workspace=workspace,
            item_id=args.item_id,
            resolution_status=args.status,
            note=args.note,
        )
    else:
        payload = latest_cycle(workspace, args.section)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
