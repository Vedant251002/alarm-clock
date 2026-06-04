# Implementation Plan — Alarm Clock CLI

- [ ] 1. Scaffold the package
  - Create `alarmclock/` package with `__init__.py` and `__main__.py`.
  - _Requirements: all_

- [ ] 2. Implement the data model (`models.py`)
  - `Alarm` dataclass, time/repeat validation, serialization, `is_due(now)`.
  - _Requirements: R1, R5_

- [ ] 3. Implement persistence (`storage.py`)
  - Resolve config dir (with `ALARMCLOCK_HOME` override), load/save JSON,
    tolerate corrupt files.
  - _Requirements: R7_

- [ ] 4. Implement cross-platform sound (`sound.py`)
  - Platform detection with graceful fallback to ASCII bell.
  - _Requirements: R5_

- [ ] 5. Implement the scheduler (`scheduler.py`)
  - Pure due-selection given a `now`, plus per-minute de-duplication.
  - _Requirements: R5_

- [ ] 6. Implement the notifier (`notifier.py`)
  - Banner + sound + snooze/dismiss prompt, TTY-aware.
  - _Requirements: R5, R6_

- [ ] 7. Implement the CLI (`cli.py`)
  - argparse subcommands: add/list/remove/enable/disable/run.
  - _Requirements: R1, R2, R3, R4, R5_

- [ ] 8. Add tests (`tests/`)
  - Unit tests for models, storage, scheduler.
  - _Requirements: R1, R5, R7_

- [ ] 9. Add README with usage examples
  - _Requirements: all_

- [ ] 10. Verify end-to-end
  - Run tests, exercise add/list/remove and `run --once`.
  - _Requirements: all_

- [ ] 11. Add `next_fire_time` helper to models (unit-testable countdown)
  - _Requirements: R8_

- [ ] 12. Implement `ansi.py` (escape helpers, VT enable, terminal size)
  - _Requirements: R8_

- [ ] 13. Implement `keyboard.py` (cross-platform non-blocking key reader)
  - _Requirements: R8_

- [ ] 14. Implement `bigclock.py` (large ASCII digit rendering)
  - _Requirements: R8_

- [ ] 15. Implement `dashboard.py` (render loop + NORMAL/ALERTING states)
  - _Requirements: R8_

- [ ] 16. Wire `dashboard` subcommand into the CLI
  - _Requirements: R8_

- [ ] 17. Tests for `next_fire_time`; verify dashboard renders one frame
  - _Requirements: R8_
