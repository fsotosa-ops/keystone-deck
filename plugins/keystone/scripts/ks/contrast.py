"""WCAG 2.x contrast checks for a brand's declared text pairs."""

from __future__ import annotations

# WCAG 2.2, success criterion 1.4.3: 4.5:1 for normal text, 3:1 for large text
# (24 px regular or 18.66 px bold and up).
THRESHOLDS = {"normal": 4.5, "large": 3.0}


def _channel(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    h = value.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) not in (6, 8):
        raise ValueError(f"not a hex colour: {value!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(value: str) -> float:
    r, g, b = (_channel(c) for c in hex_to_rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: str, bg: str) -> float:
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def check_pairs(colors: dict[str, str], pairs: list[list[str]]) -> list[dict]:
    """Return one row per pair: fg, bg, size, ratio, required, ok."""
    rows = []
    for pair in pairs:
        fg, bg = pair[0], pair[1]
        size = pair[2] if len(pair) > 2 else "normal"
        if size not in THRESHOLDS:
            raise ValueError(f"pair {pair}: size must be 'normal' or 'large'")
        for role in (fg, bg):
            if role not in colors:
                raise KeyError(f"pair {pair}: unknown colour role {role!r}")
        r = ratio(colors[fg], colors[bg])
        need = THRESHOLDS[size]
        rows.append({"fg": fg, "bg": bg, "size": size, "ratio": round(r, 2),
                     "required": need, "ok": r >= need})
    return rows
