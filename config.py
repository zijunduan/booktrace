from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "notes_dir": "data/notes",
    "last_book": "",
}


def _resolve_app_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _ensure_dirs(config: dict[str, Any] | None = None) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    notes_dir = (config or DEFAULT_CONFIG).get("notes_dir", DEFAULT_CONFIG["notes_dir"])
    _resolve_app_path(notes_dir).mkdir(parents=True, exist_ok=True)


def _normalized_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    if isinstance(raw, dict):
        for key in DEFAULT_CONFIG:
            if key in raw:
                config[key] = raw[key]
    if not isinstance(config["notes_dir"], str) or not config["notes_dir"].strip():
        config["notes_dir"] = DEFAULT_CONFIG["notes_dir"]
    if not isinstance(config["last_book"], str):
        config["last_book"] = str(config["last_book"])
    return config


def load_config() -> dict[str, Any]:
    _ensure_dirs()
    if not CONFIG_PATH.exists():
        config = DEFAULT_CONFIG.copy()
        save_config(config)
        return config

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        config = DEFAULT_CONFIG.copy()
        save_config(config)
        return config

    config = _normalized_config(raw)
    _ensure_dirs(config)
    return config


def save_config(config: dict[str, Any]) -> None:
    normalized = _normalized_config(config)
    _ensure_dirs(normalized)
    CONFIG_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_notes_dir() -> Path:
    config = load_config()
    notes_dir = _resolve_app_path(config["notes_dir"])
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir


def get_last_book() -> str:
    return str(load_config().get("last_book", ""))


def set_last_book(book: str) -> None:
    config = load_config()
    config["last_book"] = book.strip()
    save_config(config)


def set_notes_dir(notes_dir: str | Path) -> None:
    path = Path(notes_dir).expanduser()
    config = load_config()
    config["notes_dir"] = str(path)
    save_config(config)
