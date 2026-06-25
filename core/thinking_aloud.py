"""
Thinking Aloud — sesli düşünme efektleri.
JARVIS işlem yaparken doğal konuşma efektleri üretir.
"""

from __future__ import annotations

import json
import random
import threading
import time
from pathlib import Path
from typing import Any, Optional

import traceback

__all__ = ["ThinkingAloud", "create_thinking_aloud"]

BASE_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_PHRASES_PATH = BASE_DIR / "assets" / "thinking_phrases.json"


def _load_phrases(path: Optional[Path] = None) -> dict[str, list[str]]:
    """Load thinking phrases from JSON."""
    path = path or _DEFAULT_PHRASES_PATH
    defaults: dict[str, list[str]] = {
        "processing": ["Bir saniye...", "Hemen bakiyorum..."],
        "searching": ["Araştırıyorum...", "Veritabanina bakiyorum..."],
        "calculating": ["Hesapliyorum..."],
        "thinking": ["Hmm...", "Soyle dusuneyim..."],
        "error_recovery": ["Bir sorun olustu, tekrar deniyorum..."],
    }
    if not path.exists():
        return defaults
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            for k, v in loaded.items():
                if isinstance(v, list) and v:
                    defaults[k] = v
    except Exception:
        traceback.print_exc()
    return defaults


class ThinkingAloud:
    """
    Sesli düşünme motoru.

    JARVIS uzun süreli işlemler yaparken kullanıcıya doğal sesli geri bildirim verir.
    """

    def __init__(
        self,
        phrases_path: Optional[Path] = None,
        voice: str = "piper-fahrettin",
        min_interval: float = 3.0,
        max_interval: float = 8.0,
        on_phrase: Optional[callable] = None,
    ) -> None:
        self.phrases = _load_phrases(phrases_path)
        self.voice = voice
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.on_phrase = on_phrase

        self._active = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._context: str = "processing"

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self, context: str = "processing") -> None:
        """Start thinking aloud in background."""
        if self._active:
            return
        self._active = True
        self._context = context if context in self.phrases else "processing"
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        # Speak first phrase immediately
        self._speak_random()

    def stop(self) -> None:
        """Stop thinking aloud."""
        self._active = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def set_context(self, context: str) -> None:
        """Change thinking context (processing, searching, calculating, thinking, error_recovery)."""
        if context in self.phrases:
            self._context = context

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Internal ──────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            interval = random.uniform(self.min_interval, self.max_interval)
            if self._stop_event.wait(interval):
                break
            if self._active:
                self._speak_random()

    def _speak_random(self) -> None:
        """Pick and speak a random phrase from current context."""
        try:
            phrases = self.phrases.get(self._context, self.phrases.get("processing", []))
            if not phrases:
                return
            phrase = random.choice(phrases)

            if self.on_phrase:
                self.on_phrase(phrase)
            else:
                # Default: use existing TTS
                from actions.tts import speak_text
                speak_text(phrase, voice=self.voice)
        except Exception:
            traceback.print_exc()

    def get_stats(self) -> dict[str, Any]:
        return {
            "active": self._active,
            "context": self._context,
            "phrases_loaded": sum(len(v) for v in self.phrases.values()),
        }


# ── Factory ──────────────────────────────────────────────────────────────────


def create_thinking_aloud(
    voice: str = "piper-fahrettin",
    on_phrase: Optional[callable] = None,
) -> ThinkingAloud:
    """Create ThinkingAloud with sensible defaults."""
    return ThinkingAloud(voice=voice, on_phrase=on_phrase)
