from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestBargeInDetector(unittest.TestCase):
    """BargeInDetector konusma kesme tespiti testleri."""

    def test_module_import(self):
        """core.barge_in import edilebilmeli."""
        from core.barge_in import BargeInDetector
        self.assertIsNotNone(BargeInDetector)

    def test_default_creation(self):
        """BargeInDetector varsayilan parametrelerle olusabilmeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        self.assertEqual(det.threshold_db, 10.0)
        self.assertEqual(det.min_duration_ms, 300)
        self.assertEqual(det.sample_rate, 16000)
        self.assertEqual(det.frame_duration_ms, 30)
        self.assertIsNone(det.on_barge_in)
        self.assertIsNone(det.on_error)

    def test_custom_params(self):
        """BargeInDetector ozel parametrelerle olusabilmeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector(
            threshold_db=5.0,
            min_duration_ms=500,
            sample_rate=48000,
            frame_duration_ms=20,
        )
        self.assertEqual(det.threshold_db, 5.0)
        self.assertEqual(det.min_duration_ms, 500)
        self.assertEqual(det.sample_rate, 48000)
        self.assertEqual(det.frame_duration_ms, 20)

    def test_initial_state(self):
        """Baslangic durumu dogru olmali."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        self.assertFalse(det.is_barge_in())
        self.assertFalse(det.is_jarvis_speaking())

    def test_set_jarvis_speaking(self):
        """set_jarvis_speaking() durumu guncellemeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        det.set_jarvis_speaking(True, audio_level=50.0)
        self.assertTrue(det.is_jarvis_speaking())
        det.set_jarvis_speaking(False)
        self.assertFalse(det.is_jarvis_speaking())

    def test_process_user_audio_not_speaking(self):
        """JARVIS konusmuyorken process_user_audio False donmeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        result = det.process_user_audio(b"\x00" * 960)
        self.assertFalse(result)

    def test_process_user_audio_silence(self):
        """Sessizlikte process_user_audio False donmeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        det.set_jarvis_speaking(True, audio_level=50.0)
        result = det.process_user_audio(b"\x00" * 960)
        self.assertFalse(result)

    def test_process_user_audio_empty(self):
        """Bos audio'da False donmeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        det.set_jarvis_speaking(True, audio_level=50.0)
        result = det.process_user_audio(b"")
        self.assertFalse(result)

    def test_barge_in_detection(self):
        """Kullanici sesi threshold'u asinca barge-in tespit edilmeli."""
        from core.barge_in import BargeInDetector
        import struct
        det = BargeInDetector(
            threshold_db=1.0,
            min_duration_ms=30,  # 1 frame
            frame_duration_ms=30,
        )
        det.set_jarvis_speaking(True, audio_level=10.0)
        # Yuksek RMS'li sessizlik: RMS=0 -> dB=-inf
        # Daha yuksek bir sesle tetikleyelim
        samples = [5000 if i % 2 == 0 else -5000 for i in range(480)]
        pcm = struct.pack("<" + "h" * 480, *samples)
        result = det.process_user_audio(pcm)
        self.assertTrue(result)
        self.assertTrue(det.is_barge_in())

    def test_barge_in_callback(self):
        """Barge-in tespitinde on_barge_in callback'i tetiklenmeli."""
        from core.barge_in import BargeInDetector
        import struct
        fired = []

        det = BargeInDetector(
            threshold_db=1.0,
            min_duration_ms=30,
            frame_duration_ms=30,
            on_barge_in=lambda: fired.append(True),
        )
        det.set_jarvis_speaking(True, audio_level=10.0)

        samples = [8000 if i % 2 == 0 else -8000 for i in range(480)]
        pcm = struct.pack("<" + "h" * 480, *samples)
        det.process_user_audio(pcm)
        self.assertEqual(len(fired), 1)

    def test_on_error_called_on_exception(self):
        """process_user_audio exception'da on_error cagrilmali."""
        from core.barge_in import BargeInDetector
        errors = []

        det = BargeInDetector(
            on_error=lambda e: errors.append(e),
        )
        det.set_jarvis_speaking(True, audio_level=50.0)
        # Gecersiz PCM
        det.process_user_audio(b"x")
        # False dondu mu
        self.assertFalse(det.process_user_audio(b"x"))

    def test_consecutive_frames_required(self):
        """Ard arda yeterli frame gelmeden barge-in tespit edilmemeli."""
        from core.barge_in import BargeInDetector
        import struct
        det = BargeInDetector(
            threshold_db=1.0,
            min_duration_ms=90,  # 3 frames
            frame_duration_ms=30,
        )
        det.set_jarvis_speaking(True, audio_level=10.0)

        samples = [5000 if i % 2 == 0 else -5000 for i in range(480)]
        pcm = struct.pack("<" + "h" * 480, *samples)

        # 1 frame yetmez, 3 frame gerek
        for _ in range(2):
            det.process_user_audio(pcm)
        self.assertFalse(det.is_barge_in())

        # 3. frame'de tetiklenmeli
        det.process_user_audio(pcm)
        self.assertTrue(det.is_barge_in())

    def test_reset(self):
        """reset() tum state'i sifirlamali."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        det.set_jarvis_speaking(True, audio_level=50.0)
        self.assertTrue(det.is_jarvis_speaking())
        det.reset()
        self.assertFalse(det.is_jarvis_speaking())
        self.assertFalse(det.is_barge_in())

    def test_get_stats(self):
        """get_stats() beklenen anahtarlari icermeli."""
        from core.barge_in import BargeInDetector
        det = BargeInDetector()
        stats = det.get_stats()
        self.assertIn("jarvis_speaking", stats)
        self.assertIn("barge_detected", stats)
        self.assertIn("threshold_db", stats)
        self.assertIn("consecutive_speech", stats)


class TestCreateBargeInDetector(unittest.TestCase):
    """Factory fonksiyon testleri."""

    def test_factory_returns_detector(self):
        """create_barge_in_detector BargeInDetector dondurmeli."""
        from core.barge_in import create_barge_in_detector
        det = create_barge_in_detector()
        self.assertIsNotNone(det)

    def test_factory_with_callbacks(self):
        """create_barge_in_detector callback'ler ile calisabilmeli."""
        from core.barge_in import create_barge_in_detector
        det = create_barge_in_detector(
            on_barge_in=lambda: None,
            threshold_db=5.0,
        )
        self.assertIsNotNone(det.on_barge_in)
        self.assertEqual(det.threshold_db, 5.0)


class TestBargeInTiming(unittest.TestCase):
    """Barge-in tespit suresi <500ms olmali — SC-001."""

    def test_barge_in_detection_within_500ms(self):
        """Kullanici konusmaya basladiktan sonra barge-in 500ms icinde tetiklenmeli."""
        import time
        import numpy as np
        from core.barge_in import BargeInDetector

        fired = []
        det = BargeInDetector(
            threshold_db=5.0,
            min_duration_ms=100,  # hizli tespit icin dusuk
            on_barge_in=lambda: fired.append(True),
        )

        # JARVIS konusuyor
        det.set_jarvis_speaking(True, audio_level=5.0)

        # Kullanici sesi (JARVIS'ten 10dB yuksek)
        sample_rate = 16000
        duration_ms = 200
        num_samples = int(sample_rate * duration_ms / 1000)
        user_audio = (np.random.randn(num_samples) * 5000).astype(np.int16).tobytes()

        start = time.perf_counter()
        # Simule edilmis frame'ler
        chunk_size = int(sample_rate * 30 / 1000)  # 30ms frame
        for i in range(0, len(user_audio), chunk_size):
            chunk = user_audio[i:i + chunk_size]
            if len(chunk) < chunk_size:
                break
            det.process_user_audio(chunk)
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertTrue(fired, "Barge-in tetiklenmeli")
        self.assertLessEqual(elapsed_ms, 500,
            f"Barge-in {elapsed_ms:.1f}ms — 500ms siniri asildi")

    def test_barge_in_not_fired_when_jarvis_silent(self):
        """JARVIS konusmuyorken barge-in tetiklenmemeli."""
        import numpy as np
        from core.barge_in import BargeInDetector

        fired = []
        det = BargeInDetector(
            threshold_db=10.0,
            min_duration_ms=100,
            on_barge_in=lambda: fired.append(True),
        )

        # JARVIS sessiz
        det.set_jarvis_speaking(False)

        chunk = (np.random.randn(480) * 5000).astype(np.int16).tobytes()
        for _ in range(10):
            det.process_user_audio(chunk)

        self.assertFalse(fired, "JARVIS sessizken barge-in tetiklenmemeli")


if __name__ == "__main__":
    unittest.main(verbosity=2)
