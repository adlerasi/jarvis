"""
Streaming Speech-to-Text Motoru 2.0
faster-whisper + VAD + Turkish syllable fix.
"""

from __future__ import annotations

import queue
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

import traceback

from core.text_utils import fix_turkish_syllable_split

__all__ = ["StreamingSTT", "RealtimeSTT", "create_streaming_stt"]


class StreamingSTT:
    """
    Real-time streaming STT using faster-whisper.

    Features:
    - Queue-based async transcription
    - Built-in VAD filtering
    - Turkish syllable-split correction
    - Partial and final transcription callbacks
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "tr",
        beam_size: int = 1,
        best_of: int = 1,
        temperature: float = 0.0,
        condition_on_previous_text: bool = False,
        vad_filter: bool = True,
        vad_threshold: float = 0.3,
        min_speech_duration_ms: int = 300,
        min_silence_duration_ms: int = 500,
        on_transcription: Optional[Callable[[str, bool], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self.best_of = best_of
        self.temperature = temperature
        self.condition_on_previous_text = condition_on_previous_text
        self.vad_filter = vad_filter
        self.vad_threshold = vad_threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.on_transcription = on_transcription
        self.on_partial = on_partial

        self._model = None
        self._model_loaded = False
        self._running = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None

        self._audio_buffer = deque(maxlen=480000)
        self._speech_buffer = bytearray()
        self._current_text = ""
        self._final_text = ""
        self._is_speaking = False
        self._silence_start = 0.0

        # Stats
        self._last_transcription_time = 0.0
        self._transcription_count = 0
        self._total_audio_processed = 0

    # ── Model management ───────────────────────────────────────────────────────

    def load_model(self) -> bool:
        if self._model_loaded:
            return True
        try:
            from faster_whisper import WhisperModel

            model_path = self.model_path or "base"
            print(f"[StreamingSTT] Model yukleniyor: {model_path}")

            self._model = WhisperModel(
                model_path,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=8,
                num_workers=2,
            )

            # Warm-up
            dummy = np.zeros(16000, dtype=np.float32)
            list(self._model.transcribe(dummy, language=self.language, beam_size=1))

            self._model_loaded = True
            print("[StreamingSTT] Model yuklendi ve hazir")
            return True
        except ImportError:
            print("[StreamingSTT] faster-whisper kurulu degil. pip install faster-whisper")
            return False
        except Exception as exc:
            print(f"[StreamingSTT] Model yukleme hatasi: {exc}")
            traceback.print_exc()
            return False

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> bool:
        if not self.load_model():
            return False
        self._running = True
        self._thread = threading.Thread(target=self._transcription_loop, daemon=True)
        self._thread.start()
        print("[StreamingSTT] Streaming STT baslatildi")
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("[StreamingSTT] Streaming STT durduruldu")

    # ── Audio input ────────────────────────────────────────────────────────────

    def feed_audio(self, audio_data: bytes) -> None:
        """Feed PCM int16 audio chunk for transcription."""
        if not self._running:
            return
        self._audio_queue.put(audio_data)

    # ── Transcription loop ─────────────────────────────────────────────────────

    def _transcription_loop(self) -> None:
        while self._running:
            try:
                audio_data = self._audio_queue.get(timeout=0.1)
                self._process_audio_chunk(audio_data)
            except queue.Empty:
                if len(self._speech_buffer) > 0 and time.time() - self._silence_start > 1.0:
                    self._transcribe_speech_buffer()
                continue
            except Exception as exc:
                print(f"[StreamingSTT] Transkripsiyon hatasi: {exc}")
                traceback.print_exc()

    def _process_audio_chunk(self, audio_data: bytes) -> None:
        self._audio_buffer.extend(np.frombuffer(audio_data, dtype=np.int16))
        self._speech_buffer.extend(audio_data)
        buffer_duration = len(self._speech_buffer) / 2 / 16000
        if buffer_duration >= 1.0:
            self._transcribe_speech_buffer()

    def _transcribe_speech_buffer(self) -> None:
        if len(self._speech_buffer) < 3200:
            return
        try:
            audio_array = np.frombuffer(self._speech_buffer, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            start_time = time.time()
            segments, info = self._model.transcribe(
                audio_float,
                language=self.language,
                beam_size=self.beam_size,
                best_of=self.best_of,
                temperature=self.temperature,
                condition_on_previous_text=self.condition_on_previous_text,
                vad_filter=self.vad_filter,
                vad_parameters={
                    "threshold": self.vad_threshold,
                    "min_speech_duration_ms": self.min_speech_duration_ms,
                    "min_silence_duration_ms": self.min_silence_duration_ms,
                },
            )

            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
                if self.on_partial:
                    self.on_partial(segment.text.strip())

            full_text = " ".join(text_parts).strip()
            if full_text:
                full_text = fix_turkish_syllable_split(full_text)
                self._current_text = full_text
                self._final_text += " " + full_text if self._final_text else full_text
                if self.on_transcription:
                    is_final = len(self._speech_buffer) < 6400
                    self.on_transcription(full_text, is_final)

            elapsed = time.time() - start_time
            self._last_transcription_time = elapsed
            self._transcription_count += 1
            self._total_audio_processed += len(self._speech_buffer)

            overlap = int(0.5 * 16000 * 2)
            if len(self._speech_buffer) > overlap:
                self._speech_buffer = self._speech_buffer[-overlap:]
            self._silence_start = time.time()
        except Exception as exc:
            print(f"[StreamingSTT] Transkripsiyon hatasi: {exc}")
            traceback.print_exc()

    # ── Results ────────────────────────────────────────────────────────────────

    def get_current_text(self) -> str:
        return self._current_text

    def get_final_text(self) -> str:
        return self._final_text

    def clear(self) -> None:
        self._current_text = ""
        self._final_text = ""
        self._speech_buffer = bytearray()

    def get_stats(self) -> dict[str, Any]:
        return {
            "model_loaded": self._model_loaded,
            "running": self._running,
            "transcription_count": self._transcription_count,
            "last_transcription_time": self._last_transcription_time,
            "total_audio_processed_mb": self._total_audio_processed / (1024 * 1024),
            "buffer_size": len(self._speech_buffer),
        }


class RealtimeSTT:
    """
    Simplified real-time STT wrapper.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 100,
        on_text: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.stt = StreamingSTT(
            model_path=model_path,
            on_transcription=self._on_transcription,
            on_partial=self._on_partial,
        )
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.on_text = on_text
        self._partial_text = ""
        self._final_text = ""

    def _on_transcription(self, text: str, is_final: bool) -> None:
        self._final_text += " " + text if self._final_text else text
        self._partial_text = ""
        if is_final and self.on_text:
            self.on_text(self._final_text.strip())

    def _on_partial(self, text: str) -> None:
        self._partial_text = text

    def start(self) -> bool:
        return self.stt.start()

    def stop(self) -> None:
        self.stt.stop()

    def feed_chunk(self, audio_chunk: bytes) -> None:
        self.stt.feed_audio(audio_chunk)

    def get_text(self) -> str:
        return (self._final_text + " " + self._partial_text if self._partial_text else self._final_text).strip()

    def clear(self) -> None:
        self._final_text = ""
        self._partial_text = ""
        self.stt.clear()


# ── Factory ──────────────────────────────────────────────────────────────────


def create_streaming_stt(
    model_path: Optional[str] = None,
    on_text: Optional[Callable[[str], None]] = None,
) -> RealtimeSTT:
    """Create a streaming STT instance with sensible defaults."""
    return RealtimeSTT(model_path=model_path, on_text=on_text)
