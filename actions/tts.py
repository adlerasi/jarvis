"""
actions/tts.py
JARVIS TTS arayüzü - tüm sesli yanıtlar buradan geçer.
"""

from __future__ import annotations

from typing import Optional

from core.audio_system.tts_engine import get_tts_engine, speak_text

__all__ = ["speak_text", "get_tts_engine", "get_available_voices", "_edge_voice_name"]


# ── Voice mapping ─────────────────────────────────────────────


def _edge_voice_name(alias: str) -> str:
    """Map an alias (e.g. 'edge-ahmet') to a Microsoft Edge TTS voice ID.

    Falls back to ``tr-TR-AhmetNeural`` for unknown aliases.
    """
    _voice_map = {
        "edge-ahmet": "tr-TR-AhmetNeural",
        "edge-emel": "tr-TR-EmelNeural",
        "ahmet": "tr-TR-AhmetNeural",
        "emel": "tr-TR-EmelNeural",
        "tr-TR-AhmetNeural": "tr-TR-AhmetNeural",
        "tr-TR-EmelNeural": "tr-TR-EmelNeural",
    }
    return _voice_map.get(alias, "tr-TR-AhmetNeural")


# ── Engine discovery ──────────────────────────────────────────


def get_available_voices() -> list[dict[str, object]]:
    """Scan all registered TTS engines and return their availability status.

    Returns a list of dicts with keys ``name``, ``available``, and ``active``.
    """
    engine = get_tts_engine()
    active_name = engine.get_active_engine()
    result: list[dict[str, object]] = []
    for ename in engine.list_engines():
        result.append({
            "name": ename,
            "available": True,
            "active": ename == active_name,
        })
    if not result:
        result.append({
            "name": "none",
            "available": False,
            "active": False,
        })
    return result
