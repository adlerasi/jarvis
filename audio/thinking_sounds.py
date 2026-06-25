"""Thinking Sounds — vocal fillers for natural conversational delay.

Plays brief vocalizations while the LLM is processing to make
the interaction feel more natural and human-like.

Usage:
    ts = ThinkingSounds()
    ts.speak("Hmm...")  # tts via jarvis
    sound = ts.select(delay_ms=2000)  # auto-select based on delay
"""

from __future__ import annotations

import random
from typing import Optional

_THINKING_SOUNDS: dict[str, list[str]] = {
    "neutral": [
        "Hmm...",
        "Bakalim...",
        "Dusuneyim...",
    ],
    "processing": [
        "Soyle yapalim...",
        "Bir saniye...",
        "Kontrol ediyorum...",
    ],
    "uncertain": [
        "Emin degilim ama...",
        "Galiba...",
        "Sanirim...",
    ],
    "excited": [
        "Vay!",
        "Harika!",
        "Bunu sevdim!",
    ],
    "concerned": [
        "Hmm, sorun var gibi...",
        "Dikkatli olalim...",
    ],
    "thinking": [
        "Bir dakika...",
        "Su an bakiyorum...",
        "Anlamaya calisiyorum...",
    ],
}

# Thresholds in ms for sound selection
_SHORT_DELAY_MS = 1500
_LONG_DELAY_MS = 4000


class ThinkingSounds:
    """Vocal delay filler library for natural conversation flow.

    Selects and optionally plays sounds based on estimated
    LLM processing delay.
    """

    def __init__(self, sounds: Optional[dict[str, list[str]]] = None):
        self._sounds = sounds or _THINKING_SOUNDS

    # ── Selection ────────────────────────────────────────────

    @property
    def categories(self) -> list[str]:
        return list(self._sounds.keys())

    def select(self, delay_ms: float, category: str = "neutral") -> str:
        """Choose a thinking sound based on delay and category.

        Short delays (<1.5s) return shorter sounds.
        Long delays (>4s) may return multi-part sounds.
        """
        sounds = self._sounds.get(category, self._sounds["neutral"])
        if not sounds:
            return ""

        if delay_ms < _SHORT_DELAY_MS:
            # Short delay — use a minimal filler
            candidates = [s for s in sounds if len(s) < 15]
            return random.choice(candidates) if candidates else random.choice(sounds)
        elif delay_ms > _LONG_DELAY_MS:
            # Long delay — use a multi-part filler or excited/concerned
            candidates = [s for s in sounds if len(s) >= 15]
            return random.choice(candidates) if candidates else random.choice(sounds)
        else:
            return random.choice(sounds)

    def random(self, category: str = "neutral") -> str:
        """Pick a random sound from the given category."""
        sounds = self._sounds.get(category, self._sounds["neutral"])
        return random.choice(sounds) if sounds else ""

    def count(self) -> int:
        """Total number of registered sounds."""
        return sum(len(v) for v in self._sounds.values())
