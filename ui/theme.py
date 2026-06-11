"""
JARVIS UI — Theme
Color palette, fonts, sizing constants extracted from ui.py
for reuse across the ui/ package.
"""

from __future__ import annotations

# ── Renk paleti ──────────────────────────────────────────────
C_BG      = "#020c0c"
C_PRI     = "#00d4c0"
C_ORG     = "#ff6600"
C_ORG2    = "#ff9900"
C_MID     = "#006a62"
C_DIM     = "#0a2a28"
C_DIMMER  = "#061414"
C_TEXT    = "#7dfff6"
C_PANEL   = "#030f0f"
C_GREEN   = "#00ff88"
C_RED     = "#ff3344"
C_MUTED   = "#cc2255"
C_BLUE    = "#4488ff"
C_GOLD    = "#ffcc00"

# Orb durum renkleri
ORB_COLORS: dict[str, tuple[int, int, int]] = {
    "LISTENING":    (0, 255, 136),
    "SPEAKING":     (68, 136, 255),
    "THINKING":     (255, 204, 0),
    "MUTED":        (200, 30, 80),
    "PAUSED":       (30, 60, 55),
    "ERROR":        (255, 51, 68),
    "INITIALISING": (255, 51, 68),
}

STATE_HEX_COLORS = {
    "LISTENING": C_GREEN,
    "SPEAKING":  C_BLUE,
    "THINKING":  C_GOLD,
    "INITIALISING": C_RED,
    "ERROR":     C_RED,
}

# ── Boyutlar ─────────────────────────────────────────────────
W_TARGET    = 2200
H_TARGET    = 1320
LEFT_W_T    = 360
RIGHT_W_T   = 410
HDR_H       = 72
FOOTER_H    = 26
INPUT_H     = 34
CONTROL_H   = 146

VOICES = ["Charon", "Puck", "Aoede", "Kore", "Fenrir", "Leda", "Orus", "Zephyr"]

# ── Font sistemi ─────────────────────────────────────────────
FONT_BODY_FAMILY    = "Grift"
FONT_DISPLAY_FAMILY = "Grift Extra Bold"


def font_body(size: int):
    return (FONT_BODY_FAMILY, size)


def font_body_bold(size: int):
    return (FONT_BODY_FAMILY, size, "bold")


def font_display(size: int):
    return (FONT_DISPLAY_FAMILY, size)
