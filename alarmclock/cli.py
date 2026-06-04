"""Command-line interface for the alarm clock."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta

from . import __version__
from .models import Alarm, parse_repeat, parse_time
from .scheduler import Scheduler
from .sound import play_alarm
from .storage import find_alarm, load_alarms, save_alarms, store_path


# ---------------------------------------------------------------------------
# Alarm trigger / notifier (inline — only used by cmd_run)
# ---------------------------------------------------------------------------

def _trigger(alarm: Alarm, now: datetime, snooze_minutes: int):
    """Print a banner, play sound, prompt dismiss/snooze. Returns snooze datetime or None."""
    line = "=" * 44
    print(f"\n{line}\n  ALARM  {now.strftime('%H:%M')}  -  {alarm.label}\n{line}")
    play_alarm()

    if not sys.stdin or not sys.stdin.isatty():
        print("  (non-interactive: alarm sounded once)")
        return None

    while True:
        try:
            choice = input(f"  [d]ismiss / [s]nooze {snooze_minutes} min > ").strip().lower()
        except EOFError:
            return None
        if choice in ("", "d", "dismiss"):
            print("  dismissed.")
            return None
        if choice in ("s", "snooze"):
            wake = now + timedelta(minutes=snooze_minutes)
            print(f"  snoozed until {wake.strftime('%H:%M')}.")
            return wake
        print("  please type 'd' or 's'.")


def cmd_add(args: argparse.Namespace) -> int:
    alarm = Alarm(
        time=parse_time(args.time),
        label=args.label,
        repeat=parse_repeat(args.repeat),
    )
    alarms = load_alarms()
    alarms.append(alarm)
    save_alarms(alarms)
    print(f"added {alarm.id}  {alarm.time}  {alarm.label}  ({alarm.repeat_label()})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    alarms = load_alarms()
    if not alarms:
        print("no alarms set. add one with:  alarmclock add 07:30 --label \"Wake up\"")
        return 0
    alarms.sort(key=lambda a: a.time)
    print(f"{'ID':<10}{'TIME':<7}{'STATE':<9}{'REPEAT':<12}LABEL")
    for a in alarms:
        state = "on" if a.enabled else "off"
        print(f"{a.id:<10}{a.time:<7}{state:<9}{a.repeat_label():<12}{a.label}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    alarms = load_alarms()
    target = find_alarm(alarms, args.id)
    if target is None:
        print(f"error: no alarm with id '{args.id}'", file=sys.stderr)
        return 1
    alarms = [a for a in alarms if a.id != args.id]
    save_alarms(alarms)
    print(f"removed {args.id}")
    return 0


def _set_enabled(alarm_id: str, enabled: bool) -> int:
    alarms = load_alarms()
    target = find_alarm(alarms, alarm_id)
    if target is None:
        print(f"error: no alarm with id '{alarm_id}'", file=sys.stderr)
        return 1
    target.enabled = enabled
    save_alarms(alarms)
    print(f"{'enabled' if enabled else 'disabled'} {alarm_id}")
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    return _set_enabled(args.id, True)


def cmd_disable(args: argparse.Namespace) -> int:
    return _set_enabled(args.id, False)


def _fire(alarm: Alarm, now: datetime, snooze_minutes: int,
          snoozed: list[tuple[datetime, Alarm]]) -> None:
    wake = _trigger(alarm, now, snooze_minutes)
    if wake is not None:
        snoozed.append((wake, alarm))
    if not alarm.is_recurring:
        # Disable one-time alarms in the store after they fire.
        alarms = load_alarms()
        stored = find_alarm(alarms, alarm.id)
        if stored is not None and stored.enabled:
            stored.enabled = False
            save_alarms(alarms)


def cmd_run(args: argparse.Namespace) -> int:
    scheduler = Scheduler()
    snoozed: list[tuple[datetime, Alarm]] = []
    print(f"alarm clock running — watching {store_path()}")
    print("press Ctrl+C to stop.")
    try:
        while True:
            now = datetime.now()
            alarms = load_alarms()

            for alarm in scheduler.due_alarms(alarms, now):
                _fire(alarm, now, args.snooze, snoozed)

            # Handle snoozed re-fires (in-memory, not persisted).
            still_pending: list[tuple[datetime, Alarm]] = []
            for wake, alarm in snoozed:
                if now >= wake:
                    _trigger(alarm, now, args.snooze)
                else:
                    still_pending.append((wake, alarm))
            snoozed = still_pending

            if args.once:
                return 0
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    from .dashboard import Dashboard

    return Dashboard(snooze_minutes=args.snooze).run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarmclock", description="A command-line alarm clock."
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add an alarm")
    p_add.add_argument("time", help="alarm time in 24h HH:MM, e.g. 07:30")
    p_add.add_argument("--label", default="Alarm", help="label for the alarm")
    p_add.add_argument("--repeat", default=None,
                       help="comma-separated weekdays, e.g. mon,tue,wed")
    p_add.set_defaults(func=cmd_add)

    sub.add_parser("list", help="list all alarms").set_defaults(func=cmd_list)

    p_rm = sub.add_parser("remove", help="remove an alarm by id")
    p_rm.add_argument("id")
    p_rm.set_defaults(func=cmd_remove)

    p_en = sub.add_parser("enable", help="enable an alarm by id")
    p_en.add_argument("id")
    p_en.set_defaults(func=cmd_enable)

    p_dis = sub.add_parser("disable", help="disable an alarm by id")
    p_dis.add_argument("id")
    p_dis.set_defaults(func=cmd_disable)

    p_run = sub.add_parser("run", help="watch the clock and fire alarms")
    p_run.add_argument("--snooze", type=int, default=5,
                       help="snooze length in minutes (default 5)")
    p_run.add_argument("--once", action="store_true",
                       help="check a single tick and exit (for testing)")
    p_run.set_defaults(func=cmd_run)

    p_dash = sub.add_parser("dashboard", help="live full-screen TUI dashboard")
    p_dash.add_argument("--snooze", type=int, default=5,
                        help="snooze length in minutes (default 5)")
    p_dash.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
