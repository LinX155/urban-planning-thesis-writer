"""Controlled DOCX writing helper for the thesis skill.

This script writes only user-authorized text blocks. It creates a backup before
save, can inspect the document outline, append a section, or insert text after a
matching heading. It is intentionally conservative: figures, equations, fields,
citations, and complex layouts should be preserved unless the user explicitly
provides replacement content and scope.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


def ensure_docx():
    try:
        import docx  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit("Missing dependency: python-docx. Run init_thesis_workspace.ps1 first.") from exc
    return docx


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def state_root(workspace: Path) -> Path:
    return workspace / ".urban-planning-thesis-writer"


def resolve_workspace_path(workspace: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = workspace / path
    return path.resolve()


def backup_docx(workspace: Path, docx_path: Path, label: str) -> Path:
    backup_dir = state_root(workspace) / "state" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    out = backup_dir / f"{timestamp()}-{label}-{docx_path.name}"
    shutil.copy2(docx_path, out)
    return out


def style_names(document) -> set[str]:
    return {style.name for style in document.styles}


def pick_style(document, preferred: Iterable[str], fallback: str | None = None) -> str | None:
    names = style_names(document)
    for name in preferred:
        if name in names:
            return name
    return fallback if fallback in names else None


def heading_style(document, level: int) -> str | None:
    return pick_style(document, [f"Heading {level}", f"标题 {level}", f"标题{level}"])


def paragraph_style(document) -> str | None:
    return pick_style(document, ["Normal", "正文"])


def bullet_style(document) -> str | None:
    return pick_style(document, ["List Bullet", "项目符号", "列表项目"])


def insert_paragraph_after(paragraph, text: str = "", style: str | None = None):
    docx = ensure_docx()
    new_p = docx.oxml.OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = docx.text.paragraph.Paragraph(new_p, paragraph._parent)
    if text:
        new_para.add_run(text)
    if style:
        new_para.style = style
    return new_para


def parse_text_blocks(text: str) -> list[tuple[str, str, int | None]]:
    """Return (kind, text, heading_level). Supports simple Markdown headings."""
    blocks: list[tuple[str, str, int | None]] = []
    pending: list[str] = []

    def flush_pending() -> None:
        nonlocal pending
        if pending:
            blocks.append(("paragraph", "\n".join(pending).strip(), None))
            pending = []

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_pending()
            continue
        if stripped.startswith("#"):
            marker, _, rest = stripped.partition(" ")
            if marker and all(ch == "#" for ch in marker) and rest:
                flush_pending()
                level = min(len(marker), 6)
                blocks.append(("heading", rest.strip(), level))
                continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_pending()
            blocks.append(("bullet", stripped[2:].strip(), None))
            continue
        pending.append(stripped)
    flush_pending()
    return blocks


def add_blocks(document, blocks: list[tuple[str, str, int | None]]) -> int:
    count = 0
    for kind, text, level in blocks:
        if not text:
            continue
        if kind == "heading":
            style = heading_style(document, level or 1)
            para = document.add_paragraph(text)
            if style:
                para.style = style
        elif kind == "bullet":
            style = bullet_style(document)
            para = document.add_paragraph(text)
            if style:
                para.style = style
        else:
            style = paragraph_style(document)
            para = document.add_paragraph(text)
            if style:
                para.style = style
        count += 1
    return count


def insert_blocks_after(document, anchor_idx: int, blocks: list[tuple[str, str, int | None]]) -> int:
    anchor = document.paragraphs[anchor_idx]
    current = anchor
    count = 0
    for kind, text, level in blocks:
        if not text:
            continue
        style: str | None
        if kind == "heading":
            style = heading_style(document, level or 1)
        elif kind == "bullet":
            style = bullet_style(document)
        else:
            style = paragraph_style(document)
        current = insert_paragraph_after(current, text, style)
        count += 1
    return count


def find_heading(document, heading: str) -> int | None:
    target = " ".join(heading.split())
    for idx, para in enumerate(document.paragraphs):
        text = " ".join(para.text.split())
        if text == target:
            return idx
    return None


def inspect_docx(docx_path: Path) -> dict:
    docx = ensure_docx()
    document = docx.Document(str(docx_path))
    outline = []
    table_summaries = []
    for idx, para in enumerate(document.paragraphs):
        style = para.style.name if para.style is not None else ""
        text = para.text.strip()
        if text and ("Heading" in style or "标题" in style):
            outline.append({"index": idx, "style": style, "text": text[:180]})
    for idx, table in enumerate(document.tables, start=1):
        preview = ""
        if table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in table.rows[0].cells]
            preview = " | ".join([cell for cell in cells if cell][:4])[:180]
        table_summaries.append(
            {
                "index": idx,
                "rows": len(table.rows),
                "cols": len(table.columns),
                "first_row_preview": preview,
            }
        )
    header_texts = []
    footer_texts = []
    for idx, section in enumerate(document.sections, start=1):
        header = " ".join([p.text.strip() for p in section.header.paragraphs if p.text.strip()])[:180]
        footer = " ".join([p.text.strip() for p in section.footer.paragraphs if p.text.strip()])[:180]
        header_texts.append({"section": idx, "text": header})
        footer_texts.append({"section": idx, "text": footer})
    return {
        "docx": str(docx_path),
        "paragraph_count": len(document.paragraphs),
        "table_count": len(document.tables),
        "section_count": len(document.sections),
        "inline_shape_count": len(document.inline_shapes),
        "style_count": len(document.styles),
        "style_samples": sorted(style_names(document))[:40],
        "outline": outline,
        "table_summaries": table_summaries,
        "headers": header_texts,
        "footers": footer_texts,
        "guardrail": "Use exact headings and authorized edit scope before writing. Do not infer missing results or alter complex objects without explicit user material.",
    }


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_log(workspace: Path, payload: dict) -> Path:
    log_dir = state_root(workspace) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{timestamp()}-docx-writer.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def save_document(document, out_path: Path) -> None:
    document.save(str(out_path))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("--docx", required=True)

    for name in ("append", "insert-after-heading"):
        p = sub.add_parser(name)
        p.add_argument("--workspace", required=True)
        p.add_argument("--docx", required=True)
        p.add_argument("--text-file", required=True)
        p.add_argument("--save-as")
        p.add_argument("--label", default=name)
        if name == "insert-after-heading":
            p.add_argument("--heading", required=True)

    args = parser.parse_args()
    docx = ensure_docx()

    if args.command == "inspect":
        print(json.dumps(inspect_docx(Path(args.docx).resolve()), ensure_ascii=False, indent=2))
        return 0

    workspace = Path(args.workspace).resolve()
    docx_path = resolve_workspace_path(workspace, args.docx)
    out_path = resolve_workspace_path(workspace, args.save_as) if args.save_as else docx_path
    text = load_text(resolve_workspace_path(workspace, args.text_file))
    blocks = parse_text_blocks(text)
    document = docx.Document(str(docx_path))
    backup = backup_docx(workspace, docx_path, args.label)

    if args.command == "append":
        changed = add_blocks(document, blocks)
    elif args.command == "insert-after-heading":
        idx = find_heading(document, args.heading)
        if idx is None:
            raise SystemExit(f"Heading not found: {args.heading}")
        changed = insert_blocks_after(document, idx, blocks)
    else:  # pragma: no cover
        raise SystemExit(f"Unknown command: {args.command}")

    save_document(document, out_path)
    payload = {
        "command": args.command,
        "docx": str(docx_path),
        "output": str(out_path),
        "backup": str(backup),
        "paragraphs_written": changed,
        "guardrail": "Review the written range in Word. Snapshot and diff before the next write pass.",
    }
    payload["log"] = str(write_log(workspace, payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
