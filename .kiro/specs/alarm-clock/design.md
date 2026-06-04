# Design — Alarm Clock CLI

## Architecture
A small, layered, single-package application using only the Python standard
library.

```
alarmclock/
  __init__.py     # package metadata
  models.py       # Alarm dataclass + (de)serialization, time/repeat logic
  storage.py      # load/save alarms to JSON in the user config dir
  sound.py        # cross-platform beep with fallbacks
  scheduler.py    # decides which alarms are due "now"
  notifier.py     # interactive trigger: message + snooze/dismiss prompt
  cli.py          # argparse command surface; wires everything together
  __main__.py     # `python -m alarmclock`
tests/            # unit tests for models, storage, scheduler
```

### Why these boundaries
- `models` is pure logic (no I/O) so it is trivially testable.
- `storage` isolates the file format; swapping JSON for something else later
  touches one module.
- `sound` and `notifier` isolate side effects (audio, stdin/stdout).
- `scheduler` is pure given a "now" timestamp, so tests inject a fixed time.

## Data Model
`Alarm` (dataclass):
- `id: str` — short unique id (first 8 chars of a uuid4).
- `time: str` — "HH:MM" 24-hour.
- `label: str` — human label, default "Alarm".
- `repeat: list[str]` — weekday codes from {mon,tue,wed,thu,fri,sat,sun};
  empty means one-time.
- `enabled: bool` — default True.

Serialized as a JSON list of objects. The store file:
- Windows: `%APPDATA%/alarmclock/alarms.json`
- else: `~/.config/alarmclock/alarms.json`
Overridable via `ALARMCLOCK_HOME` env var (used by tests).

## Scheduling Logic
- The monitor loop wakes roughly every second.
- An alarm is "due" when:
  - `enabled` is True, AND
  - current `HH:MM` equals the alarm time, AND
  - (repeat is empty) OR (current weekday code is in `repeat`).
- De-duplication: remember the last `(alarm_id, "YYYY-MM-DD HH:MM")` fired so a
  given alarm fires once per minute, not once per second.
- One-time alarms are disabled and saved after firing.

## Sound Strategy (cross-platform, stdlib only)
Try in order, fall back gracefully:
1. Windows: `winsound.Beep` in a short pattern.
2. macOS: `afplay` of a system sound, else `say`.
3. Linux: `paplay`/`aplay` if present.
4. Universal fallback: print the ASCII bell `\a` repeatedly.
The trigger never crashes the app if audio is unavailable.

## Snooze / Dismiss Flow
When an alarm fires in an interactive terminal:
- Print a banner with time + label, start the sound.
- Prompt: `[d]ismiss / [s]nooze (default 5 min)`.
- On snooze, schedule an in-memory one-shot re-fire after N minutes (does not
  modify the stored alarm).
- If stdin is not a TTY (e.g. piped/non-interactive), just sound + message once.

## CLI Surface (argparse subcommands)
- `add TIME [--label L] [--repeat d1,d2] ` 
- `list`
- `remove ID`
- `enable ID` / `disable ID`
- `run [--snooze N] [--once]`  (`--once` checks a single tick, used in tests/demo)

## Error Handling
- Invalid time / weekday → `SystemExit` with message, non-zero exit code.
- Unknown id → message + non-zero exit.
- Corrupt JSON → start from empty store with a warning rather than crashing.

## Testing Strategy
- `models`: time parsing, repeat parsing, serialization round-trip, due-check.
- `storage`: save/load round-trip in a temp dir via `ALARMCLOCK_HOME`.
- `scheduler`: due selection with injected "now" and de-dup behavior.
Tests run via `unittest` (stdlib), no third-party deps.

## Live TUI Dashboard (R8)

### Approach
Rather than `curses` (unavailable on Windows, and we are stdlib-only), the
dashboard is built from ANSI escape sequences plus a tiny cross-platform,
non-blocking keyboard reader. This keeps zero third-party dependencies and
works on Windows, macOS, and Linux.

### New modules
```
alarmclock/
  ansi.py        # ANSI escape helpers + terminal size + enable VT on Windows
  keyboard.py    # non-blocking single-key reader (msvcrt / termios+select)
  bigclock.py    # render HH:MM:SS as large ASCII block digits
  dashboard.py   # the full-screen render + event loop
```

### ansi.py
- Constants/helpers: clear screen, move cursor home, hide/show cursor,
  truecolor/256 SGR colors, bold, reset.
- `enable_vt()`: on Windows, enable virtual-terminal processing via ctypes so
  ANSI codes render; on other platforms it is a no-op.
- `terminal_size()`: wraps `shutil.get_terminal_size` with a sane fallback.

### keyboard.py
- `KeyReader` context manager.
  - Windows: poll `msvcrt.kbhit()` / `msvcrt.getwch()`.
  - Unix: put stdin in cbreak mode with `termios`, poll with `select`.
  - `get_key(timeout)` returns a single char or None (non-blocking), so the
    render loop never stalls waiting on input.
  - Restores terminal state on exit (cooked mode, cursor shown).

### bigclock.py
- A 5-row ASCII font for digits 0-9 and ':'.
- `render(text) -> list[str]`: returns the rows for a time string so the
  dashboard can center it.

### dashboard.py — render loop
Pure-ish render: build a list of lines from current state, then paint.
- Each tick (~4 fps): read `now`, reload alarms (cheap JSON read, cached by
  mtime to avoid disk churn), compute next alarm + countdown.
- Reuse `Scheduler.due_alarms(now)` for due detection and `play_alarm()` for
  sound — no logic duplication.
- States:
  - NORMAL: big clock, date, next-alarm + countdown, alarm table, key hints.
  - ALERTING: banner flashes (color invert toggles each tick), sound plays,
    hints become `[d]ismiss  [s]nooze`. Single keypress handles the choice.
- One-time alarms auto-disable after firing (same rule as `run`), persisted via
  storage; snooze is in-memory like `run`.
- Repaint strategy: move cursor home and overwrite, padding each line to width
  to avoid artifacts; clear fully on resize. Hide cursor while running.
- Exit: `q` (or Ctrl+C) -> show cursor, reset colors, clear, restore terminal.

### Countdown / next-alarm computation
For each enabled alarm compute the next future datetime it will fire:
- one-time: today at its time if still ahead, else tomorrow.
- recurring: the nearest upcoming weekday in `repeat` at its time.
Pick the minimum; display `Xh Ym Zs`. This logic lives as a helper next to the
model so it is unit-testable with an injected `now`.

### Graceful degradation
If stdout is not a TTY, `dashboard` prints a notice and suggests `run` instead,
exiting without trying to take over the screen.
