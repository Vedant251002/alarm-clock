"""Cross-platform non-blocking single-key reader for the TUI."""

from __future__ import annotations

import sys


class KeyReader:
    """Context manager yielding single keypresses without blocking.

    Usage:
        with KeyReader() as kb:
            key = kb.get_key(timeout=0.25)  # str or None
    """

    def __init__(self) -> None:
        self._is_win = sys.platform.startswith("win")
        self._fd = None
        self._old = None

    def __enter__(self) -> "KeyReader":
        if not self._is_win:
            try:
                import termios
                import tty

                self._fd = sys.stdin.fileno()
                self._old = termios.tcgetattr(self._fd)
                tty.setcbreak(self._fd)
            except Exception:
                self._fd = None
        return self

    def __exit__(self, *exc) -> None:
        if not self._is_win and self._fd is not None and self._old is not None:
            try:
                import termios

                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)
            except Exception:
                pass

    def get_key(self, timeout: float = 0.25):
        """Return a single character if pressed within `timeout`, else None."""
        if self._is_win:
            return self._get_key_windows(timeout)
        return self._get_key_unix(timeout)

    def _get_key_windows(self, timeout: float):
        import time
        import msvcrt

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                # Swallow the second byte of special (arrow/fn) keys.
                if ch in ("\x00", "\xe0"):
                    if msvcrt.kbhit():
                        msvcrt.getwch()
                    return None
                return ch
            time.sleep(0.01)
        return None

    def _get_key_unix(self, timeout: float):
        import select

        if self._fd is None:
            return None
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            ch = sys.stdin.read(1)
            return ch or None
        return None
