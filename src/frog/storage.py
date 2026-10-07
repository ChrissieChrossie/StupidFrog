"""Remembers user choices between runs (e.g. AI quips on/off, personality)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_FILE = Path.home() / ".frog" / "settings.json"

# Earlier versions stored German keys in a different file. They are migrated once.
LEGACY_FILE = Path.home() / ".frosch" / "einstellungen.json"
_LEGACY_KEYS = {
    "ki_sprueche": "ai_quips",
    "charakter": "personality",
    "ton": "sound",
    "streiche": "pranks",
}
_LEGACY_PRANKS = {
    "fenster_oeffnen": "open_window",
    "fenster_knoepfe": "window_buttons",
    "symbole_verstecken": "hide_icons",
    "in_ordner_packen": "pack_into_box",
}


def _read(path: Path) -> dict | None:
    """Read a JSON file. None if it does not exist, {} if it is unreadable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        log.warning("Could not read %s, using defaults.", path)
        return {}


def _migrate(legacy: dict) -> dict:
    data = {_LEGACY_KEYS[key]: value for key, value in legacy.items() if key in _LEGACY_KEYS}
    if isinstance(data.get("pranks"), dict):
        data["pranks"] = {
            _LEGACY_PRANKS[key]: value
            for key, value in data["pranks"].items()
            if key in _LEGACY_PRANKS
        }
    return data


def load(path: Path = DEFAULT_FILE, legacy_path: Path = LEGACY_FILE) -> dict:
    data = _read(path)
    if data is not None:
        return data
    legacy = _read(legacy_path)
    return _migrate(legacy) if legacy else {}


def save(data: dict, path: Path = DEFAULT_FILE) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        log.warning("Could not save %s.", path)


def update(path: Path = DEFAULT_FILE, **changes) -> None:
    """Load, apply `changes` and save again."""
    save({**load(path), **changes}, path)
