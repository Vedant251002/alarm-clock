"""Cross-platform alarm sound with graceful fallbacks (stdlib only)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time


def _bell(repeat: int = 3) -> None:
    """Universal fallback: terminal bell."""
    for _ in range(repeat):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.4)


def _windows_beep() -> bool:
    try:
        import winsound  # type: ignore
    except ImportError:
        return False
    for freq in (880, 988, 1047):
        winsound.Beep(freq, 250)
    return True


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _macos_sound() -> bool:
    if shutil.which("afplay"):
        return _run(["afplay", "/System/Library/Sounds/Glass.aiff"])
    if shutil.which("say"):
        return _run(["say", "Alarm"])
    return False


def _linux_sound() -> bool:
    candidates = [
        ("paplay", ["/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"]),
        ("aplay", []),
    ]
    for tool, args in candidates:
        if shutil.which(tool) and args:
            if _run([tool, *args]):
                return True
    return False


def play_alarm() -> None:
    """Play a short alarm sound, never raising on failure."""
    try:
        if sys.platform.startswith("win"):
            if _windows_beep():
                return
        elif sys.platform == "darwin":
            if _macos_sound():
                return
        elif sys.platform.startswith("linux"):
            if _linux_sound():
                return
    except Exception:
        pass
    _bell()
