"""Thinking Sounds — vocal fillers for natural conversational delay.

Plays brief vocalizations while the LLM is processing to make
the interaction feel more natural and human-like.

Usage:
    ts = ThinkingSounds()
    ts.speak("Hmm...")  # tts via speak_text callback
    sound = ts.select(delay_ms=2000)
"""

from __future__ import annotations

import random
import threading
from typing import Callable, Optional

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

_SHORT_DELAY_MS = 1500
_LONG_DELAY_MS = 4000


class ThinkingSounds:
    """Vocal delay filler library for natural conversation flow.

    Selects and optionally plays sounds based on estimated
    LLM processing delay. Connects to TTS via a callable.

    Args:
        sounds: Custom sound dictionary (keys = categories).
        tts_callback: Callable(text: str) -> None for TTS playback.
            If None, speak() is a no-op.
    """

    def __init__(
        self,
        sounds: Optional[dict[str, list[str]]] = None,
        tts_callback: Optional[Callable[[str], None]] = None,
    ):
        self._sounds = sounds or _THINKING_SOUNDS
        self._tts_callback = tts_callback
        self._speaking = False

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
            candidates = [s for s in sounds if len(s) < 15]
            return random.choice(candidates) if candidates else random.choice(sounds)
        elif delay_ms > _LONG_DELAY_MS:
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

    # ── TTS Integration ──────────────────────────────────────

    def speak(self, text: str) -> bool:
        """Speak a thinking sound via TTS callback.

        Returns True if the sound will be played.
        Non-blocking — spawns a daemon thread for TTS.
        """
        if not text or not self._tts_callback:
            return False

        def _play():
            self._speaking = True
            try:
                self._tts_callback(text)
            finally:
                self._speaking = False

        threading.Thread(target=_play, daemon=True).start()
        return True

    def play_delayed(self, delay_ms: float, category: str = "neutral") -> str:
        """Select and play a thinking sound based on delay.

        Returns the text that was (or would be) spoken.
        """
        text = self.select(delay_ms, category)
        if text:
            self.speak(text)
        return text

    @property
    def is_speaking(self) -> bool:
        """Whether a thinking sound is currently being spoken."""
        return self._speaking
