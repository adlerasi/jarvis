"""
Barge-in — konuşma kesme tespiti ve kesilen cümle tamamlama.

JARVIS konuşurken kullanıcının konuşmasını algılar, yanıtı keser,
ve kesilen cümleyi saklar. Sonraki yanıtta kaldığı yerden devam
edebilir.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import numpy as np

import traceback

__all__ = ["BargeInDetector", "create_barge_in_detector"]


class BargeInDetector:
    """
    Konuşma kesme (barge-in) tespiti + kesilen cümle hafızası.

    JARVIS konuşurken mikrofonu dinler, kullanıcı konuştuğunda
    on_barge_in callback'ini tetikler ve o anda söylenmekte olan
    cümlenin kalan kısmını (interrupted_text) saklar.

    Kullanım:
        detector = BargeInDetector(on_barge_in=my_handler)
        detector.set_jarvis_speaking(True, audio_level=-15.0)
        detector.set_current_speech("Merhaba, bugün nasıl...")

        # Barge-in algılandığında:
        kalan = detector.get_interrupted_sentence()  # " nasıl..."
    """

    def __init__(
        self,
        threshold_db: float = 10.0,
        min_duration_ms: int = 300,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        enabled: bool = True,
        on_barge_in: Optional[Callable] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """BargeInDetector baslatir."""
        self.threshold_db = threshold_db
        self.min_duration_ms = min_duration_ms
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.enabled = enabled
        self.on_barge_in = on_barge_in
        self.on_error = on_error

        self._jarvis_speaking = False
        self._jarvis_audio_level: float = 0.0
        self._barge_detected = False

        self._consecutive_speech = 0
        self._required_frames = max(1, int(min_duration_ms / frame_duration_ms))

        self._lock = threading.Lock()

        # ── Interrupted-sentence fields ───────────────────
        self._current_speech: str = ""        # JARVIS'in o an soyledigi metin
        self._spoken_so_far: int = 0          # Kac karakteri soylendi
        self._interrupted_text: str = ""      # Kesilen kismin kendisi

    # ── Public API ────────────────────────────────────────────

    def set_jarvis_speaking(self, speaking: bool, audio_level: float = 0.0):
        """JARVIS konuşma durumunu ayarla.

        Args:
            speaking: Konuşuyor mu.
            audio_level: JARVIS ses seviyesi (dB RMS, tipik -30..-10).
        """
        with self._lock:
            self._jarvis_speaking = speaking
            self._jarvis_audio_level = audio_level
            self._barge_detected = False
            self._consecutive_speech = 0
            if not speaking:
                # Konusma bitti, kesinti metnini temizle
                self._interrupted_text = ""

    def set_current_speech(self, text: str, spoken_chars: int = 0):
        """JARVIS'in o anda soylemekte oldugu metni kaydet.

        Cagri: Orkestrator her yeni cumle basinda cagirir.
        spoken_chars=0 ise metnin tamami henuz soylenmemis sayilir.

        Args:
            text: Soylenecek tam metin.
            spoken_chars: Kac karakteri seslendirildi (0 = henuz baslamadi).
        """
        with self._lock:
            self._current_speech = text
            self._spoken_so_far = spoken_chars

    def advance_spoken(self, chars: int):
        """Soylenen karakter sayisini guncelle.

        Args:
            chars: Toplam soylenen karakter sayisi.
        """
        with self._lock:
            self._spoken_so_far = chars

    def process_user_audio(self, audio_data: bytes) -> bool:
        """Kullanıcı sesini işle ve barge-in tespit et.

        Args:
            audio_data: Kullanıcı mikrofon sesi (PCM int16, 16kHz)

        Returns:
            True: Barge-in tespit edildi
        """
        if not self.enabled:
            return False
        with self._lock:
            if not self._jarvis_speaking:
                return False

        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_array) == 0:
                return False

            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            user_level = 20 * np.log10(max(rms, 1))

            if user_level > self._jarvis_audio_level + self.threshold_db:
                with self._lock:
                    self._consecutive_speech += 1
                    if self._consecutive_speech >= self._required_frames:
                        if not self._barge_detected:
                            self._barge_detected = True
                            # Kesinti aninda kalan metni kaydet
                            self._capture_interruption()
                            if self.on_barge_in:
                                self.on_barge_in()
                        return True
            else:
                with self._lock:
                    self._consecutive_speech = max(0, self._consecutive_speech - 1)

            return False
        except Exception as exc:
            if self.on_error:
                self.on_error(exc)
            traceback.print_exc()
            return False

    # ── Interrupted-sentence API ───────────────────────────

    def _capture_interruption(self):
        """Kesinti aninda kalan metni kaydet."""
        total = len(self._current_speech)
        spoken = min(self._spoken_so_far, total)
        remaining = self._current_speech[spoken:].strip()
        self._interrupted_text = remaining

    def get_interrupted_sentence(self) -> str:
        """Kesilen cumlenin kalan kismini dondurur.

        Returns:
            Kesinti aninda soylenmemis metin parcasi.
            Bos string = kesinti yok / kesinti temizlenmis.
        """
        return self._interrupted_text

    def has_interruption(self) -> bool:
        """Kesinti kaydi var mi?"""
        return bool(self._interrupted_text)

    def clear_interruption(self):
        """Kesinti kaydini temizle (devam edildikten sonra)."""
        self._interrupted_text = ""

    # ── Status ─────────────────────────────────────────────

    def is_barge_in(self) -> bool:
        """Barge-in (konusmayi bolme) aktif mi."""
        return self._barge_detected

    def is_jarvis_speaking(self) -> bool:
        """JARVIS su anda konusuyor mu."""
        return self._jarvis_speaking

    def reset(self):
        """Barge-in durumunu sifirlar."""
        self._jarvis_speaking = False
        self._barge_detected = False
        self._consecutive_speech = 0
        self._current_speech = ""
        self._spoken_so_far = 0
        self._interrupted_text = ""

    def get_stats(self) -> dict:
        """Barge-in istatistiklerini dondurur."""
        return {
            "jarvis_speaking": self._jarvis_speaking,
            "barge_detected": self._barge_detected,
            "threshold_db": self.threshold_db,
            "consecutive_speech": self._consecutive_speech,
            "interrupted_text": self._interrupted_text,
            "spoken_so_far": self._spoken_so_far,
        }


# ── Factory ──────────────────────────────────────────────────


def create_barge_in_detector(
    on_barge_in: Optional[Callable] = None,
    threshold_db: float = 10.0,
    enabled: bool = True,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> BargeInDetector:
    """Create a barge-in detector."""
    return BargeInDetector(
        threshold_db=threshold_db,
        enabled=enabled,
        on_barge_in=on_barge_in,
        on_error=on_error,
    )
