"""
Proactive Voice — zamanlanmış sesli bildirimler.
Cron tabanlı, belirli olaylarda JARVIS'in kendiliğinden konuşması.
"""

from __future__ import annotations

import queue
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import traceback

__all__ = ["ProactiveVoice", "create_proactive_voice"]

BASE_DIR = Path(__file__).resolve().parent.parent

# Varsayılan bildirim mesajları
_DEFAULT_GREETINGS = [
    "Merhaba! Nasilsiniz?",
    "Merhaba, size nasil yardimci olabilirim?",
    "Hosgeldiniz!",
    "Gunaydin! Bugun size nasil yardimci olabilirim?",
]

_DEFAULT_REMINDERS = [
    "Bir hatirlaticiniz var, kontrol etmek ister misiniz?",
    "Hatirlaticinizi gormek ister misiniz?",
    "Planlanmis bir etkinliginiz var.",
]

_DEFAULT_SUGGESTIONS = [
    "Hava durumuna bakmak ister misiniz?",
    "Takviminizi kontrol edelim mi?",
    "Size bir sey soyleyebilir miyim?",
]


class ProactiveVoice:
    """
    Proaktif sesli bildirim motoru.

    Zamanlanmış/greater tespiti ile JARVIS kendiliğinden konuşur:
    - Karşılama mesajları
    - Hatırlatıcı bildirimleri
    - Zamanlanmış öneriler
    - Özel olay bildirimleri
    """

    def __init__(
        self,
        voice: str = "piper-fahrettin",
        on_speak: Optional[Callable[[str], None]] = None,
    ):
        self.voice = voice
        self.on_speak = on_speak

        self._queue: queue.Queue[str] = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._user_active = False
        self._last_greeting_date: Optional[str] = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def start(self):
        """Start proactive voice engine."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        print("[ProactiveVoice] Proaktif ses motoru baslatildi")

    def stop(self):
        """Stop proactive voice engine."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        print("[ProactiveVoice] Durduruldu")

    # ── Events ───────────────────────────────────────────────────────────────

    def on_user_activated(self):
        """User activated JARVIS (wake word / button)."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._last_greeting_date != today:
            self._last_greeting_date = today
            self._queue_greeting()

    def on_idle(self, duration_seconds: float):
        """User has been idle for given duration."""
        if duration_seconds > 120 and self._queue.qsize() < 3:
            msg = random.choice(_DEFAULT_SUGGESTIONS)
            self._queue_message(msg)

    def on_reminder(self, reminder_text: str):
        """Fire a reminder notification."""
        msg = f"Hatirlatici: {reminder_text}"
        self._queue_message(msg)
        try:
            from core.notification import notify
            notify("Hatırlatıcı", reminder_text, priority="normal")
        except Exception:
            pass

    def on_custom(self, message: str):
        """Queue a custom proactive message."""
        self._queue_message(message)

    def set_user_active(self, active: bool):
        """Set whether user is currently interacting."""
        self._user_active = active

    # ── Queue ────────────────────────────────────────────────────────────────

    def _queue_greeting(self):
        msg = random.choice(_DEFAULT_GREETINGS)
        self._queue_message(msg)

    def _queue_message(self, message: str):
        if not self._user_active:
            self._queue.put(message)
            print(f"[ProactiveVoice] Kuyruga eklendi: {message}")

    def _worker_loop(self):
        while self._running:
            try:
                message = self._queue.get(timeout=1.0)
                if not self._user_active:
                    self._speak(message)
            except queue.Empty:
                continue
            except Exception:
                traceback.print_exc()

    def _speak(self, message: str):
        """Speak the message using configured voice."""
        try:
            if self.on_speak:
                self.on_speak(message)
            else:
                from actions.tts import speak_text
                speak_text(message, voice=self.voice)
        except Exception:
            traceback.print_exc()

    # ── Info ─────────────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    def get_stats(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "voice": self.voice,
            "user_active": self._user_active,
        }


# ── Factory ──────────────────────────────────────────────────────────────────


def create_proactive_voice(
    voice: str = "piper-fahrettin",
    on_speak: Optional[Callable[[str], None]] = None,
) -> ProactiveVoice:
    """Create a ProactiveVoice instance."""
    return ProactiveVoice(voice=voice, on_speak=on_speak)
