from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import subprocess
import sys

from config import get_notes_dir


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("_", name.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned


def _validate_text(value: str, field_name: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty")
    return text


def get_book_note_path(book: str) -> Path:
    book_name = _validate_text(book, "book")
    filename = sanitize_filename(book_name)
    if not filename:
        raise ValueError("book name cannot be used as a filename")
    return get_notes_dir() / f"{filename}.md"


def ensure_book_file(book: str) -> Path:
    book_name = _validate_text(book, "book")
    path = get_book_note_path(book_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {book_name}\n", encoding="utf-8")
    return path


def _entry_lines(time_text: str, thought: str) -> list[str]:
    lines = thought.replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    first, *rest = lines
    entry = [f"- {time_text} {first.strip()}"]
    entry.extend(f"  {line.rstrip()}" for line in rest)
    return entry


def _append_to_date_block(content: str, date_text: str, entry: list[str]) -> str:
    heading = f"## {date_text}"
    lines = content.splitlines()

    for index, line in enumerate(lines):
        if line.strip() != heading:
            continue

        block_end = len(lines)
        for probe in range(index + 1, len(lines)):
            if lines[probe].startswith("## "):
                block_end = probe
                break

        insert_at = block_end
        while insert_at > index + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1

        lines[insert_at:insert_at] = entry

        next_index = insert_at + len(entry)
        if next_index < len(lines) and lines[next_index].strip() != "":
            lines.insert(next_index, "")

        return "\n".join(lines).rstrip() + "\n"

    if lines and lines[-1].strip() != "":
        lines.append("")
    lines.extend([heading, "", *entry])
    return "\n".join(lines).rstrip() + "\n"


def save_thought(book: str, thought: str) -> Path:
    book_name = _validate_text(book, "book")
    thought_text = _validate_text(thought, "thought")
    path = ensure_book_file(book_name)

    now = datetime.now()
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H:%M")
    entry = _entry_lines(time_text, thought_text)

    content = path.read_text(encoding="utf-8")
    updated = _append_to_date_block(content, date_text, entry)
    path.write_text(updated, encoding="utf-8")
    return path


def open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return

    subprocess.Popen(["xdg-open", str(path)])
