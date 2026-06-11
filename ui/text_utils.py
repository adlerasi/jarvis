"""
JARVIS UI — Text utilities
Pure text-parsing functions extracted from JarvisUI.
"""

from __future__ import annotations


def _split_summary_lines(text: str, limit: int = 4) -> list[str]:
    """Split comma-separated summary text into at most *limit* lines."""
    raw = (text or "").strip()
    if not raw:
        return []
    raw = raw.replace(" ve ", ", ")
    parts = [part.strip(" .") for part in raw.split(",") if part.strip()]
    return parts[:limit]


def _parse_weather_card(text: str) -> dict:
    """Parse a weather-summary string into a display card dict."""
    if not text or "alınamadı" in text.lower() or "alınamadi" in text.lower():
        return {
            "city": "Istanbul",
            "primary": "--",
            "details": ["Hava durumu alınamadı."],
        }

    prefix, _, body = text.partition(":")
    city = "Istanbul"
    if " için" in prefix:
        city = prefix.split(" için", 1)[0].strip().title()

    details = [part.strip(" .") for part in body.split(",") if part.strip()]
    primary = "--"
    if details:
        primary = details[0].replace(" derece", "°C")
    return {
        "city": city,
        "primary": primary,
        "details": details[1:4] or ["Anlık veri hazır."],
    }


def _parse_health_card(text: str) -> list[str]:
    """Parse a health-summary string into a list of lines."""
    if not text or "alınamadı" in text.lower() or "alınamadi" in text.lower():
        return ["Sağlık verisi alınamadı."]
    lines = _split_summary_lines(text, limit=4)
    return lines or ["Sağlık özeti hazır değil."]
