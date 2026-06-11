"""
Streaming Text-to-Speech — sentence-by-sentence playback.
Reuses existing TTS backends from actions.tts.
"""

from __future__ import annotations

import queue
import re
import threading
import time
from typing import Callable, Optional

import traceback

__all__ = ["StreamingTTS", "TTSBuffer"]

_SENTENCE_SPLITTER = re.compile(
    r"(?<=[.?!;])\s+|(?<=\n)\s*",
)

_ABBREVIATIONS = {
    "dr.", "dr", "mr.", "mr", "mrs.", "mrs", "ms.", "ms",
    "prof.", "prof", "doç.", "doç", "yrd.", "yrd",
    "st.", "st", "no.", "no", "bkz.", "bkz",
    "vs.", "vs", "vb.", "vb", "örn.", "örn",
    "sn.", "sn", "s.", "s", "p.", "p",
}


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving abbreviations."""
    parts = _SENTENCE_SPLITTER.split(text)
    sentences: list[str] = []
    buffer = ""

    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        buffer = (buffer + " " + stripped).strip()
        # Check if buffer ends with a sentence-ending punctuation
        last_char = buffer[-1] if buffer else ""
        if last_char in ".!?;" and buffer.lower().rstrip(".") not in _ABBREVIATIONS:
            sentences.append(buffer)
            buffer = ""
        elif last_char == "\n":
            sentences.append(buffer.rstrip("\n"))
            buffer = ""
        # Hard cap at 500 chars to prevent overly long sentences
        elif len(buffer) > 500:
            sentences.append(buffer)
            buffer = ""

    if buffer:
        sentences.append(buffer)

    return [s.strip() for s in sentences if s.strip()]


class TTSBuffer:
    """Thread-safe sentence queue for TTS."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._cancel = threading.Event()

    def put(self, sentence: str):
        self._queue.put(sentence)

    def get(self, timeout: float = 1.0) -> Optional[str]:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def cancel(self):
        self._cancel.set()
        # Drain queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    @property
    def is_cancelled(self) -> bool:
        return self._cancel.is_set()

    def reset(self):
        self._cancel.clear()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def qsize(self) -> int:
        return self._queue.qsize()


class StreamingTTS:
    """
    Streaming TTS engine — plays sentences as they become available.

    Allows conversational flow where speech starts before the full text is ready.
    """

    def __init__(
        self,
        voice: str = "piper-fahrettin",
        on_start: Optional[Callable] = None,
        on_done: Optional[Callable] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        self.voice = voice
        self.on_start = on_start
        self.on_done = on_done
        self.on_error = on_error

        self._buffer = TTSBuffer()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = threading.Event()
        self._paused.set()  # Not paused by default
        self._current_sentence: Optional[str] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str, blocking: bool = False):
        """Queue text for TTS playback."""
        if not text or not text.strip():
            self._fire_done()
            return
        sentences = _split_sentences(text)
        self.speak_streaming(sentences, blocking)

    def speak_streaming(self, sentences: list[str], blocking: bool = False):
        """Queue multiple sentences, playing each as available."""
        if not sentences:
            self._fire_done()
            return

        if not self._running:
            self._start_worker()

        for s in sentences:
            if s:
                self._buffer.put(s)

        if blocking:
            while self._buffer.qsize() > 0 or self._current_sentence:
                time.sleep(0.1)

    def stop(self):
        """Cancel current and queued speech."""
        self._buffer.cancel()
        self._current_sentence = None
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def pause(self):
        self._paused.clear()

    def resume(self):
        self._paused.set()

    def is_speaking(self) -> bool:
        return self._running or self._buffer.qsize() > 0

    def set_voice(self, voice_id: str):
        self.voice = voice_id

    def get_stats(self) -> dict:
        return {
            "voice": self.voice,
            "running": self._running,
            "queued": self._buffer.qsize(),
            "paused": not self._paused.is_set(),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _start_worker(self):
        self._running = True
        self._buffer.reset()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def _worker_loop(self):
        try:
            if self.on_start:
                self.on_start()

            while self._running and not self._buffer.is_cancelled:
                self._paused.wait()
                sentence = self._buffer.get(timeout=0.5)
                if sentence is None:
                    continue
                self._current_sentence = sentence
                try:
                    self._play_sentence(sentence)
                except Exception as exc:
                    print(f"[StreamingTTS] Worker sentence hatasi (devam): {exc}")
                    traceback.print_exc()
                self._current_sentence = None

        except Exception as exc:
            if self.on_error:
                self.on_error(exc)
            traceback.print_exc()
        finally:
            self._running = False
            self._fire_done()
            # Auto-restart if more data arrived while dying
            if self._buffer.qsize() > 0 and not self._buffer.is_cancelled:
                self._start_worker()

    def _play_sentence(self, sentence: str):
        """Play one sentence via existing TTS backend."""
        try:
            from actions.tts import speak_text
            speak_text(sentence, blocking=True, voice=self.voice)
        except Exception as exc:
            print(f"[StreamingTTS] Oynatma hatasi: {exc}")
            traceback.print_exc()

    def _fire_done(self):
        try:
            if self.on_done:
                self.on_done()
        except Exception as exc:
            print(f"[StreamingTTS] on_done callback hatasi: {exc}")
            traceback.print_exc()
