"""Core data model for alarms. Pure logic, no I/O."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Weekday codes indexed to match datetime.weekday() (Mon=0 .. Sun=6).
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def new_id() -> str:
    """Return a short, reasonably unique id."""
    return uuid.uuid4().hex[:8]


def parse_time(value: str) -> str:
    """Validate and normalize an 'HH:MM' 24-hour time string."""
    try:
        parsed = datetime.strptime(value.strip(), "%H:%M")
    except ValueError:
        raise ValueError(f"invalid time '{value}', expected 24h HH:MM (e.g. 07:30)")
    return parsed.strftime("%H:%M")


def parse_repeat(value: str | None) -> list[str]:
    """Parse a comma-separated list of weekday codes into a normalized list."""
    if not value:
        return []
    days: list[str] = []
    for raw in value.split(","):
        code = raw.strip().lower()[:3]
        if code not in WEEKDAYS:
            raise ValueError(
                f"invalid day '{raw.strip()}', use any of: {', '.join(WEEKDAYS)}"
            )
        if code not in days:
            days.append(code)
    # Keep a stable weekday ordering for display.
    return [d for d in WEEKDAYS if d in days]


@dataclass
class Alarm:
    time: str
    label: str = "Alarm"
    repeat: list[str] = field(default_factory=list)
    enabled: bool = True
    id: str = field(default_factory=new_id)

    @property
    def is_recurring(self) -> bool:
        return bool(self.repeat)

    def is_due(self, now: datetime) -> bool:
        """True if this alarm should fire at the given moment."""
        if not self.enabled:
            return False
        if now.strftime("%H:%M") != self.time:
            return False
        if self.repeat and WEEKDAYS[now.weekday()] not in self.repeat:
            return False
        return True

    def next_fire_time(self, now: datetime) -> datetime | None:
        """Return the next datetime this alarm will fire at/after `now`.

        Returns None if disabled. Seconds/microseconds are dropped so the
        comparison is minute-aligned.
        """
        if not self.enabled:
            return None
        hour, minute = (int(p) for p in self.time.split(":"))
        base = now.replace(second=0, microsecond=0)
        candidate = base.replace(hour=hour, minute=minute)
        if not self.repeat:
            # One-time: today if still ahead of (or equal to) now, else tomorrow.
            if candidate < base:
                candidate += timedelta(days=1)
            return candidate
        # Recurring: scan the next 7 days for the nearest matching weekday.
        for offset in range(0, 8):
            day = candidate + timedelta(days=offset)
            if WEEKDAYS[day.weekday()] in self.repeat and day >= base:
                return day
        return None

    def repeat_label(self) -> str:
        if not self.repeat:
            return "once"
        if self.repeat == WEEKDAYS:
            return "daily"
        if self.repeat == WEEKDAYS[:5]:
            return "weekdays"
        if self.repeat == WEEKDAYS[5:]:
            return "weekends"
        return ",".join(self.repeat)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "label": self.label,
            "repeat": self.repeat,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        return cls(
            id=data.get("id") or new_id(),
            time=parse_time(data["time"]),
            label=data.get("label", "Alarm"),
            repeat=parse_repeat(",".join(data.get("repeat", [])) or None),
            enabled=bool(data.get("enabled", True)),
        )
