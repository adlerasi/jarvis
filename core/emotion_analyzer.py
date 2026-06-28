"""Emotion Analyzer — voice-tone-based emotion estimation.

Analyzes audio features (RMS energy, spectral characteristics,
speech rate approximation) to estimate the user's emotional state.

Works with raw PCM int16 audio chunks at 16 kHz.

Usage:
    ea = EmotionAnalyzer()
    emotion = ea.analyze(audio_bytes)  # -> "neutral"
    print(ea.current_emotion, ea.confidence)
"""

from __future__ import annotations

import json
import math
import os
import time
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np

_EMOTION_PROFILES: dict[str, dict] = {
    "neutral":  {"rms_low": 0.01, "rms_high": 0.15, "tilt": 0.0},
    "happy":    {"rms_low": 0.08, "rms_high": 0.35, "tilt": 0.3},
    "sad":      {"rms_low": 0.0,  "rms_high": 0.08, "tilt": -0.3},
    "angry":    {"rms_low": 0.20, "rms_high": 0.50, "tilt": 0.5},
    "excited":  {"rms_low": 0.15, "rms_high": 0.45, "tilt": 0.4},
    "calm":     {"rms_low": 0.0,  "rms_high": 0.06, "tilt": -0.2},
    "surprised": {"rms_low": 0.10, "rms_high": 0.40, "tilt": 0.2},
}

_EMOTION_ORDER = list(_EMOTION_PROFILES.keys())
_EMOTION_COLORS: dict[str, str] = {
    "neutral":   "#00ff88",
    "happy":     "#ffdd00",
    "sad":       "#4488ff",
    "angry":     "#ff3344",
    "excited":   "#ff8800",
    "calm":      "#88ddff",
    "surprised": "#ff44ff",
}


class EmotionAnalyzer:
    """Estimates emotion from raw PCM audio features.

    Uses a simple energy + spectral model:
    - RMS energy -> arousal level (calm -> excited)
    - Spectral centroid approximation -> valence (sad -> happy)

    Maintains a rolling window to smooth predictions and logs
    emotion changes to a JSON history file.
    """

    def __init__(
        self,
        window_size: int = 15,
        sample_rate: int = 16000,
        frame_ms: int = 30,
        history_path: str | Path = "memory/emotion_history.json",
    ):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_ms / 1000)
        self._window = deque(maxlen=window_size)
        self._current_emotion = "neutral"
        self._confidence = 0.0
        self._frames_analyzed = 0

        # Emotion change tracking
        self._last_logged_emotion: str | None = None
        self._history_path = Path(history_path)
        self._history: list[dict] = []
        self._load_history()

    # ── Public API ───────────────────────────────────────────

    def analyze(self, audio_bytes: bytes) -> str:
        """Analyze a single audio chunk and return estimated emotion.

        Logs to history when emotion changes.

        Args:
            audio_bytes: PCM int16 mono audio, 16 kHz preferred.

        Returns:
            Emotion label: neutral, happy, sad, angry, excited, calm, surprised.
        """
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        if len(audio_array) == 0:
            return self._current_emotion

        features = self._extract_features(audio_array)
        self._window.append(features)
        self._frames_analyzed += 1

        if len(self._window) >= 3:
            emotion, confidence = self._classify()
            if confidence > 0.2:
                if emotion != self._current_emotion:
                    self._log_change(emotion, confidence)
                self._current_emotion = emotion
                self._confidence = confidence

        return self._current_emotion

    def analyze_text(self, text: str) -> str:
        """Quick emotion guess from text content.

        Used when audio is not available (e.g., text commands).
        Logs to history when emotion changes.
        """
        text_lower = text.lower()
        if any(w in text_lower for w in ("sinirli", "kizgin", "of", "yeter")):
            emotion = "angry"
        elif any(w in text_lower for w in ("uzgun", "kotu", "mutsuz", "canim sikkin")):
            emotion = "sad"
        elif any(w in text_lower for w in ("harika", "muthis", "cok iyi", "super")):
            emotion = "happy"
        elif any(w in text_lower for w in ("vay", "sasirt", "gercekten", "oha")):
            emotion = "surprised"
        elif any(w in text_lower for w in ("sakin", "rahat", "iyiyim")):
            emotion = "calm"
        else:
            emotion = "neutral"

        if emotion != self._current_emotion:
            self._log_change(emotion, 0.5)
        self._current_emotion = emotion
        self._confidence = 0.5
        return emotion

    # ── Read-only properties ─────────────────────────────────

    @property
    def current_emotion(self) -> str:
        return self._current_emotion

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def color(self) -> str:
        return _EMOTION_COLORS.get(self._current_emotion, "#00ff88")

    def get_stats(self) -> dict:
        return {
            "emotion": self._current_emotion,
            "confidence": round(self._confidence, 3),
            "frames_analyzed": self._frames_analyzed,
            "history_entries": len(self._history),
        }

    # ── History API ──────────────────────────────────────────

    def get_history(self, limit: int = 100) -> list[dict]:
        """Return recent emotion history entries, newest first."""
        return list(reversed(self._history[-limit:]))

    def get_timeline(self, since: float = 0) -> list[dict]:
        """Return entries after a unix timestamp."""
        return [e for e in self._history if e["t"] >= since]

    def get_emotion_summary(self, since: float = 3600) -> dict:
        """Summarize dominant emotions in the given time window.

        Args:
            since: Lookback seconds from now (default: 1 hour).

        Returns:
            {emotion: count, dominant: str, total_entries: int}
        """
        cutoff = time.time() - since
        recent = [e for e in self._history if e["t"] >= cutoff]
        if not recent:
            return {"dominant": "neutral", "counts": {}, "total_entries": 0}

        counts: dict[str, int] = {}
        for e in recent:
            em = e["e"]
            counts[em] = counts.get(em, 0) + 1
        dominant = max(counts, key=counts.get)
        return {"dominant": dominant, "counts": counts, "total_entries": len(recent)}

    def clear_history(self):
        """Wipe all history entries."""
        self._history.clear()
        self._save_history()

    # ── Internal: history persistence ────────────────────────

    def _log_change(self, emotion: str, confidence: float):
        """Record an emotion change to in-memory history."""
        entry = {
            "t": time.time(),
            "e": emotion,
            "c": round(confidence, 3),
        }
        self._history.append(entry)
        self._last_logged_emotion = emotion
        # Persist every 5 entries or on emotion change
        if len(self._history) % 5 == 0:
            self._save_history()

    def _load_history(self):
        """Load persisted history from JSON file."""
        try:
            if self._history_path.exists() and self._history_path.stat().st_size > 2:
                with open(self._history_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._history = data[-1000:]  # cap at 1000
        except (json.JSONDecodeError, OSError):
            self._history = []

    def _save_history(self):
        """Write history to JSON file."""
        try:
            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            # Keep last 1000 entries
            data = self._history[-1000:]
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ── Feature extraction ───────────────────────────────────

    def _extract_features(self, audio: np.ndarray) -> dict:
        if len(audio) < 2:
            return {"rms": 0.0, "tilt": 0.0, "zcr": 0.0}

        audio = audio / max(np.max(np.abs(audio)), 1)

        rms = float(np.sqrt(np.mean(audio ** 2)))

        zcr = float(np.mean(np.abs(np.diff(np.sign(audio)))) / 2) if len(audio) > 1 else 0.0

        diff = np.diff(audio)
        tilt = float(np.mean(diff ** 2)) / max(rms + 1e-8, 1e-8)
        tilt = min(max(tilt * 0.1, -1.0), 1.0)

        return {"rms": rms, "tilt": tilt, "zcr": zcr}

    def _classify(self) -> tuple[str, float]:
        """Rolling window classification."""
        if not self._window:
            return ("neutral", 0.0)

        avg_rms = np.mean([f["rms"] for f in self._window])
        avg_tilt = np.mean([f["tilt"] for f in self._window])

        best_match = "neutral"
        best_score = 0.0

        for emotion, profile in _EMOTION_PROFILES.items():
            rms_score = self._score_in_range(
                avg_rms, profile["rms_low"], profile["rms_high"]
            )
            tilt_score = self._score_in_range(
                avg_tilt, -0.5 + profile["tilt"], 0.5 + profile["tilt"]
            )
            score = rms_score * 0.6 + tilt_score * 0.4

            if score > best_score:
                best_score = score
                best_match = emotion

        return (best_match, best_score)

    @staticmethod
    def _score_in_range(value: float, low: float, high: float) -> float:
        """Linear score: 1.0 if in range, tapering to 0 outside."""
        if low <= value <= high:
            return 1.0
        dist = min(abs(value - low), abs(value - high))
        return max(0.0, 1.0 - dist * 5.0)
