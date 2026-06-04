"""Persistence layer: load/save alarms as JSON in the user config dir."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .models import Alarm


def config_dir() -> Path:
    """Resolve the directory where alarms are stored.

    Honors ALARMCLOCK_HOME (used by tests), then falls back to the platform
    config location.
    """
    override = os.environ.get("ALARMCLOCK_HOME")
    if override:
        return Path(override)
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "alarmclock"
    return Path.home() / ".config" / "alarmclock"


def store_path() -> Path:
    return config_dir() / "alarms.json"


def load_alarms() -> list[Alarm]:
    """Load alarms, tolerating a missing or corrupt file."""
    path = store_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"warning: could not read {path} ({exc}); starting empty",
              file=sys.stderr)
        return []
    alarms: list[Alarm] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            alarms.append(Alarm.from_dict(item))
        except (KeyError, ValueError) as exc:
            print(f"warning: skipping invalid alarm {item!r} ({exc})",
                  file=sys.stderr)
    return alarms


def save_alarms(alarms: list[Alarm]) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [a.to_dict() for a in alarms]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_alarm(alarms: list[Alarm], alarm_id: str) -> Alarm | None:
    for alarm in alarms:
        if alarm.id == alarm_id:
            return alarm
    return None
