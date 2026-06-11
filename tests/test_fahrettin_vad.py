from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent


class TestFahrettinVAD(unittest.TestCase):
    """FahrettinVAD wrapper import, config ve API testleri.

    is_speech() -> Tuple[bool, float] dondurur, plain bool degil.
    """

    def test_module_import(self):
        """core.fahrettin_vad import edilebilmeli."""
        from core.fahrettin_vad import FahrettinVAD
        self.assertIsNotNone(FahrettinVAD)

    def test_default_creation(self):
        """FahrettinVAD varsayilan parametrelerle olusabilmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        self.assertIsNotNone(vad._engine)
        self.assertEqual(vad.engine_name, "silero")

    def test_custom_energy_threshold(self):
        """FahrettinVAD ozel energy_threshold ile olusabilmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD(energy_threshold=75.0)
        self.assertEqual(vad._engine.energy_threshold, 75.0)

    def test_custom_engine_name(self):
        """engine parametresi engine_name'e yansimali."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD(engine="energy")
        self.assertEqual(vad.engine_name, "energy")

    def test_custom_sample_rate(self):
        """sample_rate VADEngine'e aktarilir."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD(sample_rate=48000)
        self.assertEqual(vad._engine.sample_rate, 48000)

    def test_debug_log_flag(self):
        """debug_log=True sorunsuz ayarlanabilmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD(debug_log=True)
        self.assertTrue(vad.debug_log)

    def test_is_speech_returns_tuple(self):
        """is_speech() (bool, float) tuple dondurmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        result = vad.is_speech(b"\x00" * 960, sample_rate=16000)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], (bool, np.bool_))
        self.assertIsInstance(result[1], float)

    def test_is_speech_silence(self):
        """Sessizlikte ilk eleman False olmali."""
        from core.fahrettin_vad import FahrettinVAD
        import numpy as np
        vad = FahrettinVAD(engine="energy")
        speech, confidence = vad.is_speech(b"\x00" * 960, sample_rate=16000)
        self.assertFalse(speech)

    def test_is_speech_high_energy(self):
        """Yuksek enerjili frame'de ilk eleman True olmali."""
        from core.fahrettin_vad import FahrettinVAD
        import struct
        vad = FahrettinVAD(engine="energy", energy_threshold=5.0)
        samples = [8000 if i % 2 == 0 else -8000 for i in range(480)]
        pcm = struct.pack("<" + "h" * 480, *samples)
        speech, confidence = vad.is_speech(pcm, sample_rate=16000)
        self.assertTrue(speech)
        self.assertGreater(confidence, 0.0)

    def test_is_speech_too_short(self):
        """Cok kisa audio'da exception yakalanir, (False, 0.0) doner."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        speech, confidence = vad.is_speech(b"\x00" * 10, sample_rate=16000)
        self.assertFalse(speech)
        self.assertEqual(confidence, 0.0)

    def test_is_speech_different_rates(self):
        """Farkli sample_rate'lerde calisabilmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        for rate in (48000, 44100, 16000):
            frame_len = int(rate * 0.03) * 2
            speech, confidence = vad.is_speech(b"\x00" * frame_len, sample_rate=rate)
            self.assertIsInstance(speech, (bool, np.bool_))

    def test_is_speaking_initial(self):
        """Baslangicta is_speaking False olmali."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        self.assertFalse(vad.is_speaking())

    def test_reset(self):
        """reset hata firlatmamali ve metrics'i sifirlamali."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        vad.is_speech(b"\x00" * 960)
        self.assertGreater(vad._total_frames, 0)
        vad.reset()
        self.assertEqual(vad._total_frames, 0)
        self.assertEqual(vad._speech_frames, 0)
        self.assertIsNotNone(vad._engine)

    def test_get_debug_stats(self):
        """get_debug_stats() beklenen anahtarlari icermeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        stats = vad.get_debug_stats()
        self.assertIn("fahrettin_errors", stats)
        self.assertIn("fahrettin_speech_frames", stats)
        self.assertIn("fahrettin_total_frames", stats)
        self.assertIn("fahrettin_speech_ratio", stats)
        self.assertIn("engine", stats)

    def test_get_mic_level(self):
        """get_mic_level() 0.0-1.0 arasi float dondurmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        level = vad.get_mic_level()
        self.assertGreaterEqual(level, 0.0)
        self.assertLessEqual(level, 1.0)

    def test_repr(self):
        """__repr__ anlamli string dondurmeli."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        r = repr(vad)
        self.assertIn("FahrettinVAD", r)
        self.assertIn("engine=", r)

    def test_config_dict(self):
        """config dict ile FahrettinVAD yapilandirilabilmeli."""
        from core.fahrettin_vad import FahrettinVAD
        cfg = {"vad": {"fahrettin": {"engine": "energy", "energy_threshold": 30.0}}}
        vad = FahrettinVAD(config=cfg)
        self.assertEqual(vad.engine_name, "energy")
        self.assertEqual(vad._engine.energy_threshold, 30.0)

    def test_multiple_reset(self):
        """Ard arda reset cagrilari hata firlatmamali."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        for _ in range(5):
            vad.reset()

    def test_errors_tracked_on_bad_frame(self):
        """Gecersiz frame'de error sayisi artmali."""
        from core.fahrettin_vad import FahrettinVAD
        vad = FahrettinVAD()
        vad.is_speech(b"", sample_rate=16000)
        stats = vad.get_debug_stats()
        self.assertGreaterEqual(stats["fahrettin_errors"], 0)


class TestCreateFahrettinVAD(unittest.TestCase):
    """Factory fonksiyon testleri."""

    def test_factory_returns_fahrettinvad(self):
        """create_fahrettin_vad FahrettinVAD dondurmeli."""
        from core.fahrettin_vad import create_fahrettin_vad
        vad = create_fahrettin_vad()
        self.assertIsNotNone(vad)
        self.assertIsInstance(vad, object)

    def test_factory_with_config(self):
        """create_fahrettin_vad config ile calisabilmeli."""
        from core.fahrettin_vad import create_fahrettin_vad
        cfg = {"vad": {"fahrettin": {"engine": "energy"}}}
        vad = create_fahrettin_vad(config=cfg)
        self.assertEqual(vad.engine_name, "energy")


if __name__ == "__main__":
    unittest.main(verbosity=2)
