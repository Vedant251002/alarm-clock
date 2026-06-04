# Requirements — Alarm Clock CLI

## Overview
A command-line alarm clock written in Python. No web UI, no GUI, no database.
Alarms are managed through subcommands and persisted to a local JSON file. A
long-running `run` command monitors the clock and triggers due alarms with an
audible sound and an on-screen message, with the option to snooze or dismiss.

## Goals
- Simple, dependency-free (standard library only) so it runs anywhere Python runs.
- Cross-platform alarm sound (Windows / macOS / Linux) with a graceful fallback.
- Persist alarms between runs in a human-readable file.
- Support both one-time and recurring (weekly) alarms.

## Non-Goals
- No GUI, web server, or React frontend.
- No external database or network services.
- No multi-user accounts or sync.

## User Stories & Acceptance Criteria

### R1 — Add an alarm
As a user, I want to add an alarm at a specific time so it goes off later.
- WHEN I run `add 07:30` THEN a new alarm is stored for 07:30 and an id is shown.
- WHEN I pass `--label "Wake up"` THEN the label is stored with the alarm.
- WHEN I pass `--repeat mon,tue,wed` THEN the alarm recurs on those weekdays.
- WHEN no repeat is given THEN the alarm is one-time (fires once, then disables).
- IF the time is not valid 24h `HH:MM` THEN the command exits with a clear error.

### R2 — List alarms
As a user, I want to see all my alarms and their state.
- WHEN I run `list` THEN each alarm shows id, time, label, repeat, enabled state.
- WHEN there are no alarms THEN a friendly "no alarms" message is shown.

### R3 — Remove an alarm
As a user, I want to delete an alarm I no longer need.
- WHEN I run `remove <id>` for an existing alarm THEN it is deleted and confirmed.
- IF the id does not exist THEN a clear error is shown and exit code is non-zero.

### R4 — Enable / disable an alarm
As a user, I want to temporarily turn an alarm off without deleting it.
- WHEN I run `enable <id>` or `disable <id>` THEN the alarm's state toggles.

### R5 — Run the monitor and trigger alarms
As a user, I want the program to watch the clock and alert me when an alarm is due.
- WHEN `run` is active AND an enabled alarm's time matches the current minute
  (and weekday, if recurring) THEN the alarm sound plays and a message is shown.
- An alarm fires at most once per matching minute (no repeated firing in 60s).
- WHEN a one-time alarm fires THEN it is automatically disabled afterward.

### R6 — Snooze / dismiss
As a user, when an alarm goes off I want to snooze or dismiss it.
- WHEN an alarm fires interactively THEN I can dismiss it or snooze N minutes.
- WHEN I snooze THEN the alarm re-fires after the snooze interval.

### R7 — Persistence
As a user, I want my alarms to survive restarts.
- Alarms are saved to a JSON file under the user config directory.
- The file is created on first use and is valid, human-readable JSON.

### R8 — Live TUI dashboard
As a user, I want a full-screen live dashboard so I can see the clock and my
alarms at a glance and have alarms fire right inside the view.
- WHEN I run `dashboard` THEN a full-screen view shows a large live clock that
  ticks every second.
- THE dashboard shows the next upcoming alarm and a live countdown to it.
- THE dashboard lists all alarms with time, state, repeat, and label, and
  highlights the next one to fire.
- WHEN an alarm becomes due THEN the dashboard enters an alerting state (visual
  flash + sound) and lets me dismiss `d` or snooze `s` with single keypresses.
- WHEN I press `q` THEN the dashboard exits cleanly and restores the terminal.
- THE dashboard must be cross-platform and stdlib-only (no curses dependency),
  using ANSI sequences and degrading gracefully if the terminal lacks support.
