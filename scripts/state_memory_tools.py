"""State helpers for long-running thesis collaboration memory.

This script turns diff evidence and agent judgments into durable state files so
later write passes can protect user edits without blindly generalizing them.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def state_root(workspace: Path) -> Path:
    return workspace / ".urban-planning-thesis-writer"


def resolve_workspace_path(workspace: Path, raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    text = raw_path.strip()
    if not text:
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


def normalize_entry(text: str, section: str, evidence: str | None) -> dict:
    return {
        "text": text.strip(),
        "section": section,
        "evidence": evidence,
        "recorded_at": timestamp(),
    }


def merge_entries(existing: list, new_values: list[str], section: str, evidence: str | None) -> list:
    normalized = []
    seen = set()

    for item in existing:
        if isinstance(item, str):
            entry = {"text": item, "section": None, "evidence": None, "recorded_at": None}
        else:
            entry = item
        text = entry.get("text", "").strip()
        if text and text not in seen:
            normalized.append(entry)
            seen.add(text)

    for value in new_values:
        text = value.strip()
        if text and text not in seen:
            normalized.append(normalize_entry(text, section, evidence))
            seen.add(text)

    return normalized


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def remember_review(
    workspace: Path,
    section: str,
    summary_file: Path | None,
    stable: list[str],
    tentative: list[str],
    rejected: list[str],
    completed: list[str],
    pending: list[str],
    facts: list[str],
    questions: list[str],
) -> dict:
    root = state_root(workspace)
    memory_path = root / "state" / "memory" / "user_revision_preferences.json"
    section_path = root / "state" / "memory" / "section_memory.json"
    progress_path = root / "state" / "progress.json"
    history_path = root / "state" / "memory" / "review_history.jsonl"

    memory = load_json(
        memory_path,
        {
            "stable_preferences": [],
            "tentative_observations": [],
            "rejected_generalizations": [],
            "last_reviewed_section": None,
            "updated_at": None,
        },
    )
    progress = load_json(
        progress_path,
        {
            "completed_sections": [],
            "pending_sections": [],
            "last_snapshot": None,
            "last_backup": None,
            "last_review_section": None,
            "last_review_summary": None,
            "review_rounds": 0,
            "recent_diff_summaries": [],
        },
    )
    section_memory = load_json(section_path, {"sections": {}})

    evidence = str(summary_file) if summary_file else None
    memory["stable_preferences"] = merge_entries(memory.get("stable_preferences", []), stable, section, evidence)
    memory["tentative_observations"] = merge_entries(memory.get("tentative_observations", []), tentative, section, evidence)
    memory["rejected_generalizations"] = merge_entries(memory.get("rejected_generalizations", []), rejected, section, evidence)
    memory["last_reviewed_section"] = section
    memory["updated_at"] = timestamp()

    summary_payload = load_json(summary_file, {}) if summary_file and summary_file.exists() else None
    section_entry = section_memory.setdefault("sections", {}).setdefault(
        section,
        {
            "review_rounds": 0,
            "stable_preferences": [],
            "tentative_observations": [],
            "facts_confirmed": [],
            "open_questions": [],
            "last_summary_file": None,
            "updated_at": None,
        },
    )
    section_entry["review_rounds"] = int(section_entry.get("review_rounds", 0)) + 1
    section_entry["stable_preferences"] = merge_entries(section_entry.get("stable_preferences", []), stable, section, evidence)
    section_entry["tentative_observations"] = merge_entries(section_entry.get("tentative_observations", []), tentative, section, evidence)
    section_entry["facts_confirmed"] = merge_entries(section_entry.get("facts_confirmed", []), facts, section, evidence)
    section_entry["open_questions"] = merge_entries(section_entry.get("open_questions", []), questions, section, evidence)
    section_entry["last_summary_file"] = evidence
    section_entry["updated_at"] = timestamp()

    progress["completed_sections"] = sorted({*(progress.get("completed_sections", [])), *completed})
    progress["pending_sections"] = sorted({*(progress.get("pending_sections", [])), *pending})
    progress["last_review_section"] = section
    progress["last_review_summary"] = evidence
    progress["review_rounds"] = int(progress.get("review_rounds", 0)) + 1
    recent = list(progress.get("recent_diff_summaries", []))
    if evidence:
        recent.append(evidence)
    progress["recent_diff_summaries"] = recent[-10:]

    event = {
        "recorded_at": timestamp(),
        "section": section,
        "summary_file": evidence,
        "stable_preferences": stable,
        "tentative_observations": tentative,
        "rejected_generalizations": rejected,
        "facts_confirmed": facts,
        "open_questions": questions,
        "completed_sections": completed,
        "pending_sections": pending,
        "summary_excerpt": summary_payload,
    }

    write_json(memory_path, memory)
    write_json(section_path, section_memory)
    write_json(progress_path, progress)
    append_jsonl(history_path, event)
    return event


def latest_review(workspace: Path) -> dict:
    root = state_root(workspace)
    memory_path = root / "state" / "memory" / "user_revision_preferences.json"
    section_path = root / "state" / "memory" / "section_memory.json"
    progress_path = root / "state" / "progress.json"
    return {
        "memory": load_json(memory_path, {}),
        "section_memory": load_json(section_path, {}),
        "progress": load_json(progress_path, {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_review = sub.add_parser("remember-review")
    p_review.add_argument("--workspace", required=True)
    p_review.add_argument("--section", required=True)
    p_review.add_argument("--summary-file")
    p_review.add_argument("--stable", action="append", default=[])
    p_review.add_argument("--tentative", action="append", default=[])
    p_review.add_argument("--rejected", action="append", default=[])
    p_review.add_argument("--completed-section", action="append", default=[])
    p_review.add_argument("--pending-section", action="append", default=[])
    p_review.add_argument("--fact", action="append", default=[])
    p_review.add_argument("--question", action="append", default=[])

    p_latest = sub.add_parser("latest-review")
    p_latest.add_argument("--workspace", required=True)

    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    if args.command == "remember-review":
        event = remember_review(
            workspace=workspace,
            section=args.section,
            summary_file=resolve_workspace_path(workspace, args.summary_file),
            stable=args.stable,
            tentative=args.tentative,
            rejected=args.rejected,
            completed=args.completed_section,
            pending=args.pending_section,
            facts=args.fact,
            questions=args.question,
        )
        print(json.dumps(event, ensure_ascii=False, indent=2))
    elif args.command == "latest-review":
        print(json.dumps(latest_review(workspace), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
