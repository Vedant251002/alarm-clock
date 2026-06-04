"""Render a time string as large ASCII block digits (5 rows tall)."""

from __future__ import annotations

# Each glyph is 5 rows tall. Width varies; a trailing space separates glyphs.
_FONT = {
    "0": [" __ ", "|  |", "|  |", "|  |", "|__|"],
    "1": ["    ", "   |", "   |", "   |", "   |"],
    "2": [" __ ", "   |", " __|", "|   ", "|__ "],
    "3": [" __ ", "   |", " __|", "   |", " __|"],
    "4": ["    ", "|  |", "|__|", "   |", "   |"],
    "5": [" __ ", "|   ", "|__ ", "   |", " __|"],
    "6": [" __ ", "|   ", "|__ ", "|  |", "|__|"],
    "7": [" __ ", "   |", "   |", "   |", "   |"],
    "8": [" __ ", "|  |", "|__|", "|  |", "|__|"],
    "9": [" __ ", "|  |", "|__|", "   |", " __|"],
    ":": ["   ", " . ", "   ", " . ", "   "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}

HEIGHT = 5


def render(text: str) -> list[str]:
    """Return 5 strings forming the big-digit rendering of `text`."""
    rows = ["" for _ in range(HEIGHT)]
    for ch in text:
        glyph = _FONT.get(ch, _FONT[" "])
        for i in range(HEIGHT):
            rows[i] += glyph[i] + " "
    return rows


def width(text: str) -> int:
    rendered = render(text)
    return max((len(r) for r in rendered), default=0)
