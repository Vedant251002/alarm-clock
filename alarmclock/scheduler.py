"""Pure scheduling logic: pick due alarms and de-duplicate per minute."""

from __future__ import annotations

from datetime import datetime

from .models import Alarm


class Scheduler:
    """Selects due alarms and ensures each fires at most once per minute."""

    def __init__(self) -> None:
        # Remembers "alarm_id@YYYY-MM-DD HH:MM" keys already fired.
        self._fired: set[str] = set()

    @staticmethod
    def _key(alarm: Alarm, now: datetime) -> str:
        return f"{alarm.id}@{now.strftime('%Y-%m-%d %H:%M')}"

    def due_alarms(self, alarms: list[Alarm], now: datetime) -> list[Alarm]:
        """Return alarms due at `now` that have not already fired this minute."""
        due: list[Alarm] = []
        for alarm in alarms:
            if alarm.is_due(now):
                key = self._key(alarm, now)
                if key not in self._fired:
                    self._fired.add(key)
                    due.append(alarm)
        return due
