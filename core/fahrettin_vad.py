"""
FahrettinVAD — Unified VAD wrapper for J.A.R.V.I.S.

Wraps VADEngine with debug metrics, config-driven thresholds, and
a simple is_speech(chunk, sample_rate) interface that replaces
the duplicated inline energy VAD in ollama_provider.py.

Usage:
    vad = FahrettinVAD(config=audio_config)
    is_speech, confidence = vad.is_speech(audio_bytes, sample_rate=48000)
    print(vad.get_debug_stats())  # metrics snapshot
"""

from __future__ import annotations

import time
import traceback
from collections import deque
from typing import Any, Dict, Optional, Tuple

import numpy as np

from core.vad_engine import VADEngine


class FahrettinVAD:
    """
    Unified VAD wrapper with:

    * Config-driven energy threshold (default 50.0, was 400+ in inline VAD).
    * Debug metric collection (RMS, noise floor, speech ratio).
    * Auto-downsampling via the underlying VADEngine.
    * Thread-safe is_speech() for use from both Ollama and Gemini providers.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        engine: str = "silero",
        energy_threshold: float = 50.0,
        sample_rate: int = 16000,
        debug_log: bool = False,
    ):
        # -- Pull from YAML config if provided, else use defaults --
        if config and isinstance(config, dict):
            vad_cfg = config.get("vad", {})
            fc = vad_cfg.get("fahrettin", {})
            engine = fc.get("engine", engine)
            energy_threshold = float(fc.get("energy_threshold", energy_threshold))
            debug_log = bool(fc.get("debug_log", debug_log))

        self.debug_log = debug_log
        self.engine_name = engine

        # Internal VADEngine — the real workhorse
        self._engine = VADEngine(
            sample_rate=sample_rate,
            frame_duration_ms=30,
            aggressiveness=2,
            engine=engine,
            energy_threshold=energy_threshold,
        )

        # --- Debug metrics ---
        self._rms_history = deque(maxlen=200)        # last 200 RMS values
        self._threshold_history = deque(maxlen=200)   # last 200 thresholds
        self._speech_frames = 0
        self._total_frames = 0
        self._last_rms: float = 0.0
        self._last_threshold: float = 0.0
        self._errors: int = 0

        if self.debug_log:
            print(f"[FahrettinVAD] Engine={engine}, threshold={energy_threshold}")

    # ── Public API ──────────────────────────────────────────────────────────

    def is_speech(
        self, audio_frame: bytes, sample_rate: int = 16000
    ) -> Tuple[bool, float]:
        """
        Return (is_speech, confidence) for one audio frame.

        *sample_rate* can be 48000, 44100, 16000 — auto-downsampled to 16 kHz.
        Thread-safe lock is held inside VADEngine.
        """
        try:
            is_speech, confidence = self._engine.process_frame(
                audio_frame, sample_rate=sample_rate
            )
            self._total_frames += 1
            if is_speech:
                self._speech_frames += 1

            # Always collect RMS for mic level indicator (lightweight)
            self._collect_metrics(audio_frame, sample_rate)

            return is_speech, confidence

        except Exception:
            self._errors += 1
            traceback.print_exc()
            return False, 0.0

    def is_speaking(self) -> bool:
        """Convenience: current speech state from the state machine."""
        return self._engine.is_speaking()

    def reset(self) -> None:
        """Reset VAD state machine and metrics."""
        self._engine.reset()
        self._rms_history.clear()
        self._threshold_history.clear()
        self._speech_frames = 0
        self._total_frames = 0
        self._last_rms = 0.0
        self._last_threshold = 0.0
        self._errors = 0

    # ── Debug / metrics ────────────────────────────────────────────────────

    def get_mic_level(self) -> float:
        """Return normalized microphone level 0.0–1.0 for UI indicator."""
        # RMS for 16-bit audio: typical silence < 50, speech 200–5000+
        rms = self._last_rms
        if rms < 1.0:
            return 0.0
        level = min(1.0, rms / 8000.0)
        return level

    def get_debug_stats(self) -> Dict[str, Any]:
        """Return a snapshot of current VAD metrics for UI/logging."""
        stats = self._engine.get_stats()
        stats.update({
            "fahrettin_errors": self._errors,
            "fahrettin_speech_frames": self._speech_frames,
            "fahrettin_total_frames": self._total_frames,
            "fahrettin_last_rms": round(self._last_rms, 2),
            "fahrettin_last_threshold": round(self._last_threshold, 2),
            "fahrettin_speech_ratio": (
                round(self._speech_frames / max(1, self._total_frames), 4)
            ),
        })
        return stats

    def _collect_metrics(self, audio_frame: bytes, sample_rate: int) -> None:
        """Collect RMS + threshold for debug display."""
        try:
            if len(audio_frame) < 2:
                return
            arr = np.frombuffer(audio_frame, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(arr ** 2)))
            self._last_rms = rms
            self._rms_history.append(rms)
            nf = self._engine._noise_floor
            if nf is not None:
                th = max(self._engine.energy_threshold, nf * 3.0)
            else:
                th = self._engine.energy_threshold * 10
            self._last_threshold = th
            self._threshold_history.append(th)
            if self.debug_log and self._total_frames % 50 == 0:
                print(
                    f"[FahrettinVAD] RMS={rms:.1f}  "
                    f"threshold={th:.1f}  "
                    f"noise_floor={nf:.1f}"
                )
        except Exception:
            pass  # metrics collection must never crash the audio pipeline

    def __repr__(self) -> str:
        return (
            f"FahrettinVAD(engine={self.engine_name}, "
            f"errors={self._errors}, "
            f"total_frames={self._total_frames})"
        )


# ── Factory ────────────────────────────────────────────────────────────────

def create_fahrettin_vad(
    config: Optional[Dict[str, Any]] = None,
    engine: str = "silero",
    energy_threshold: float = 50.0,
    debug_log: bool = False,
) -> FahrettinVAD:
    """Convenience factory."""
    return FahrettinVAD(
        config=config,
        engine=engine,
        energy_threshold=energy_threshold,
        debug_log=debug_log,
    )
