"""
JARVIS UI — Drawing utilities
Canvas helper functions extracted from JarvisUI for reuse.
"""

from __future__ import annotations

import math
from ui.theme import C_BG, C_DIM, C_PRI, C_TEXT, ORB_COLORS


def _ac(r: int, g: int, b: int, a: int) -> str:
    """Alpha-composite a colour against C_BG background."""
    f = max(0, min(255, int(a))) / 255.0
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"


def _bar(c, x, y, w, h, pct, color):
    """Draw a horizontal bar."""
    c.create_rectangle(x, y, x+w, y+h, fill="#061212", outline=C_DIM, width=1)
    fw = max(1, int(w * pct / 100))
    c.create_rectangle(x+1, y+1, x+fw, y+h-1, fill=color, outline="")


def _sparkline(c, x, y, w, h, data):
    """Draw a sparkline chart."""
    c.create_rectangle(x, y, x+w, y+h, fill="#050e0e", outline=C_DIM, width=1)
    n = len(data)
    if n < 2:
        return
    step = (w - 2) / (n - 1) if n > 1 else 0
    h2 = h - 2
    coords = []
    for i, v in enumerate(data):
        coords.append(x + 1 + i * step)
        coords.append(y + h - 1 - int(h2 * min(v, 100) / 100))
    c.create_line(*coords, fill=C_PRI, width=1, smooth=True)


def _bracket(c, x0, y0, pw, ph, col=None, bl=12):
    """Draw corner brackets around a rectangle."""
    col = col or C_PRI
    for bx, by, sx, sy in [(x0, y0, 1, 1), (x0+pw, y0, -1, 1),
                            (x0, y0+ph, 1, -1), (x0+pw, y0+ph, -1, -1)]:
        c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
        c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)


def _draw_info_card(c, x0, y0, pw, ph, title, accent=C_PRI,
                    focus: float = 0.0, dimmed: bool = False):
    """Draw an info card with optional focus glow."""
    glow = int(55 + 120 * focus)
    border = accent if focus > 0.08 else ("#35504d" if dimmed else _ac(0, 120, 112, 190))
    fill = "#071111" if dimmed else "#030d0d"
    c.create_rectangle(x0, y0, x0+pw, y0+ph, fill=fill, outline="")
    if focus > 0.08:
        for inset in range(3):
            c.create_rectangle(
                x0-inset, y0-inset, x0+pw+inset, y0+ph+inset,
                outline=_ac(0, 255, 136, max(12, glow - inset * 28)),
                width=1,
            )
    _bracket(c, x0, y0, pw, ph, col=border, bl=10)
    from ui.theme import C_DIM
    title_fill = "#6f7d7b" if dimmed else accent
    line_fill = "#173130" if dimmed else C_DIM
    c.create_text(x0+14, y0+14, text=title, fill=title_fill,
                  font=("Grift Extra Bold", 10), anchor="w")
    c.create_line(x0+12, y0+28, x0+pw-12, y0+28, fill=line_fill)


def _orb_rgb(state: str, paused: bool) -> tuple[int, int, int]:
    """Resolve orb colour for the current state."""
    key = "PAUSED" if paused else state
    return ORB_COLORS.get(key, ORB_COLORS["LISTENING"])
