from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import re

import config


DATE_HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
THOUGHT_RE = re.compile(r"^-\s+(\d{2}:\d{2})\s+(.*)$")


@dataclass(frozen=True)
class BookSummary:
    title: str
    path: Path
    thought_count: int
    last_modified: float


@dataclass(frozen=True)
class Thought:
    date: str
    time: str
    content: str


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def _read_title(path: Path) -> str:
    for line in _read_lines(path):
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    return path.stem


def list_books() -> list[BookSummary]:
    notes_dir = config.get_notes_dir()
    books: list[BookSummary] = []

    for path in notes_dir.glob("*.md"):
        try:
            stat = path.stat()
        except OSError:
            continue

        thoughts = parse_book_notes(path)
        books.append(
            BookSummary(
                title=_read_title(path),
                path=path,
                thought_count=len(thoughts),
                last_modified=stat.st_mtime,
            )
        )

    return sorted(books, key=lambda book: book.last_modified, reverse=True)


def parse_book_notes(path: Path) -> list[Thought]:
    thoughts: list[Thought] = []
    current_date = ""
    pending: Thought | None = None

    def flush_pending() -> None:
        nonlocal pending
        if pending is not None:
            thoughts.append(pending)
            pending = None

    for line in _read_lines(path):
        date_match = DATE_HEADING_RE.match(line)
        if date_match:
            flush_pending()
            current_date = date_match.group(1)
            continue

        thought_match = THOUGHT_RE.match(line)
        if thought_match and current_date:
            flush_pending()
            pending = Thought(
                date=current_date,
                time=thought_match.group(1),
                content=thought_match.group(2).strip(),
            )
            continue

        if pending is not None and line.startswith("  "):
            continuation = line.strip()
            if continuation:
                pending = Thought(
                    date=pending.date,
                    time=pending.time,
                    content=f"{pending.content}\n{continuation}",
                )

    flush_pending()
    return thoughts


def get_random_thought() -> tuple[str, Thought] | None:
    choices: list[tuple[str, Thought]] = []
    for book in list_books():
        for thought in parse_book_notes(book.path):
            choices.append((book.title, thought))

    if not choices:
        return None
    return random.choice(choices)
