"""ANSI escape helpers for the TUI. Stdlib only, cross-platform."""

from __future__ import annotations

import os
import shutil
import sys

ESC = "\x1b"
CLEAR = f"{ESC}[2J"
HOME = f"{ESC}[H"
HIDE_CURSOR = f"{ESC}[?25l"
SHOW_CURSOR = f"{ESC}[?25h"
RESET = f"{ESC}[0m"
BOLD = f"{ESC}[1m"
CLEAR_LINE = f"{ESC}[K"


def move(row: int, col: int) -> str:
    """Cursor to 1-based (row, col)."""
    return f"{ESC}[{row};{col}H"


def fg(r: int, g: int, b: int) -> str:
    return f"{ESC}[38;2;{r};{g};{b}m"


def bg(r: int, g: int, b: int) -> str:
    return f"{ESC}[48;2;{r};{g};{b}m"


def enable_vt() -> bool:
    """Enable ANSI/VT processing on Windows consoles. No-op elsewhere.

    Returns True if escape sequences should work.
    """
    if not sys.platform.startswith("win"):
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = wintypes.DWORD()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return bool(kernel32.SetConsoleMode(handle, new_mode))
    except Exception:
        return False


def terminal_size() -> tuple[int, int]:
    """Return (columns, rows) with a sane fallback."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return max(size.columns, 20), max(size.lines, 10)


def supports_tui() -> bool:
    """True if stdout looks like an interactive terminal."""
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"
