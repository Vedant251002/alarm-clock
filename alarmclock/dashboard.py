"""Full-screen live TUI dashboard. Stdlib only, cross-platform."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

from . import ansi, bigclock
from .keyboard import KeyReader
from .models import Alarm
from .scheduler import Scheduler
from .sound import play_alarm
from .storage import find_alarm, load_alarms, save_alarms, store_path

# Palette (truecolor).
DIM = ansi.fg(120, 130, 140)
ACCENT = ansi.fg(80, 200, 250)
GOOD = ansi.fg(120, 220, 140)
WARN = ansi.fg(250, 180, 70)
ALERT_BG = ansi.bg(200, 40, 40)
WHITE = ansi.fg(235, 240, 245)


def _fmt_countdown(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    if total < 0:
        total = 0
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _next_alarm(alarms: list[Alarm], now: datetime):
    """Return (alarm, fire_time) for the soonest upcoming alarm, or (None, None)."""
    best = None
    best_time = None
    for alarm in alarms:
        fire = alarm.next_fire_time(now)
        if fire is None:
            continue
        if best_time is None or fire < best_time:
            best, best_time = alarm, fire
    return best, best_time


class Dashboard:
    def __init__(self, snooze_minutes: int = 5) -> None:
        self.snooze_minutes = snooze_minutes
        self.scheduler = Scheduler()
        self.snoozed: list[tuple[datetime, Alarm]] = []
        self.alerting: list[Alarm] = []
        self.flash = False
        self._last_size = (0, 0)

    # ---- data ----
    def _load(self) -> list[Alarm]:
        return load_alarms()

    def _disable_one_time(self, alarm: Alarm) -> None:
        if alarm.is_recurring:
            return
        alarms = load_alarms()
        stored = find_alarm(alarms, alarm.id)
        if stored is not None and stored.enabled:
            stored.enabled = False
            save_alarms(alarms)

    # ---- rendering ----
    def _frame(self, now: datetime, alarms: list[Alarm], cols: int, rows: int) -> list[str]:
        if self.alerting:
            return self._frame_alerting(now, cols)
        return self._frame_normal(now, alarms, cols, rows)

    def _center(self, text: str, cols: int) -> str:
        pad = max((cols - len(text)) // 2, 0)
        return " " * pad + text

    def _frame_normal(self, now, alarms, cols, rows) -> list[str]:
        lines: list[str] = []
        title = "ALARM CLOCK  -  live dashboard"
        lines.append(ACCENT + self._center(title, cols) + ansi.RESET)
        lines.append("")

        # Big clock.
        clock = bigclock.render(now.strftime("%H:%M:%S"))
        cw = bigclock.width(now.strftime("%H:%M:%S"))
        pad = " " * max((cols - cw) // 2, 0)
        for r in clock:
            lines.append(WHITE + pad + r + ansi.RESET)
        lines.append(DIM + self._center(now.strftime("%A, %d %B %Y"), cols) + ansi.RESET)
        lines.append("")

        # Next alarm + countdown.
        nxt, nxt_time = _next_alarm(alarms, now)
        if nxt is not None and nxt_time is not None:
            cd = _fmt_countdown(nxt_time - now)
            label = f"next: {nxt.time}  {nxt.label}   in {cd}"
            lines.append(GOOD + self._center(label, cols) + ansi.RESET)
        else:
            lines.append(DIM + self._center("no upcoming alarms", cols) + ansi.RESET)
        lines.append("")

        # Alarm table.
        if alarms:
            header = f"{'ID':<10}{'TIME':<7}{'STATE':<7}{'REPEAT':<12}LABEL"
            indent = " " * max((cols - 52) // 2, 0)
            lines.append(indent + DIM + header + ansi.RESET)
            for a in sorted(alarms, key=lambda x: x.time):
                marker = ACCENT + ">" + ansi.RESET if nxt and a.id == nxt.id else " "
                state_txt = "on" if a.enabled else "off"
                state_col = (GOOD if a.enabled else DIM) + f"{state_txt:<7}" + ansi.RESET
                row = (f"{a.id:<10}{a.time:<7}{state_col}"
                       f"{DIM}{a.repeat_label():<12}{ansi.RESET}{a.label}")
                lines.append(indent[:-1] + marker + row)
        else:
            lines.append(DIM + self._center("no alarms - add one with: alarmclock add 07:30", cols) + ansi.RESET)

        # Footer hint.
        lines.append("")
        hint = "[q]uit"
        lines.append(DIM + self._center(hint, cols) + ansi.RESET)
        return lines

    def _frame_alerting(self, now, cols) -> list[str]:
        lines: list[str] = []
        labels = ", ".join(a.label for a in self.alerting)
        bar = ALERT_BG + WHITE + ansi.BOLD
        block = " " * cols
        banner_on = self.flash
        for _ in range(3):
            lines.append((bar + block + ansi.RESET) if banner_on else "")
        clock = bigclock.render(now.strftime("%H:%M"))
        cw = bigclock.width(now.strftime("%H:%M"))
        pad = " " * max((cols - cw) // 2, 0)
        color = WARN if banner_on else WHITE
        for r in clock:
            lines.append(color + pad + r + ansi.RESET)
        lines.append("")
        lines.append((ansi.BOLD + WARN + self._center("* ALARM *  " + labels, cols) + ansi.RESET))
        lines.append("")
        lines.append(WHITE + self._center("[d]ismiss    [s]nooze", cols) + ansi.RESET)
        return lines

    def _paint(self, lines: list[str], cols: int, rows: int, full: bool) -> None:
        out = [ansi.HOME]
        if full:
            out.append(ansi.CLEAR)
        for i in range(rows):
            text = lines[i] if i < len(lines) else ""
            out.append(ansi.move(i + 1, 1) + text + ansi.CLEAR_LINE)
        sys.stdout.write("".join(out))
        sys.stdout.flush()

    # ---- input handling ----
    def _handle_alerting_key(self, key: str, now: datetime) -> None:
        if key in ("d", "D"):
            for a in self.alerting:
                self._disable_one_time(a)
            self.alerting = []
        elif key in ("s", "S"):
            wake = now + timedelta(minutes=self.snooze_minutes)
            for a in self.alerting:
                self.snoozed.append((wake, a))
                self._disable_one_time(a)
            self.alerting = []

    # ---- main loop ----
    def run(self) -> int:
        if not ansi.supports_tui():
            print("dashboard needs an interactive terminal; try: alarmclock run")
            return 1
        ansi.enable_vt()
        sys.stdout.write(ansi.HIDE_CURSOR + ansi.CLEAR)
        try:
            with KeyReader() as kb:
                while True:
                    now = datetime.now()
                    alarms = self._load()

                    # Due detection (reuses scheduler de-dup).
                    for a in self.scheduler.due_alarms(alarms, now):
                        self.alerting.append(a)
                        play_alarm()

                    # Snooze re-fires.
                    pending = []
                    for wake, a in self.snoozed:
                        if now >= wake:
                            self.alerting.append(a)
                            play_alarm()
                        else:
                            pending.append((wake, a))
                    self.snoozed = pending

                    cols, rows = ansi.terminal_size()
                    resized = (cols, rows) != self._last_size
                    self._last_size = (cols, rows)
                    self.flash = not self.flash

                    frame = self._frame(now, alarms, cols, rows)
                    self._paint(frame, cols, rows, full=resized)

                    key = kb.get_key(timeout=0.25)
                    if key is None:
                        continue
                    if self.alerting:
                        self._handle_alerting_key(key, now)
                    elif key in ("q", "Q"):
                        return 0
        except KeyboardInterrupt:
            return 0
        finally:
            sys.stdout.write(ansi.SHOW_CURSOR + ansi.RESET + ansi.CLEAR + ansi.HOME)
            sys.stdout.flush()
