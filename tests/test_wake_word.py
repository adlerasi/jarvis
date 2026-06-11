from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestWakeWordEngine(unittest.TestCase):
    """WakeWordEngine import, config ve API testleri.

    Backend chain: openWakeWord -> Porcupine -> energy.
    Ortamda openWakeWord/Porcupine yoksa energy fallback kullanilir.
    """

    def test_module_import(self):
        """core.wake_word import edilebilmeli."""
        from core.wake_word import WakeWordEngine
        self.assertIsNotNone(WakeWordEngine)

    def test_default_creation(self):
        """WakeWordEngine varsayilan parametrelerle olusabilmeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy"})
        self.assertIsNotNone(engine)
        self.assertIn(engine._engine_name, ("openwakeword", "porcupine", "energy"))
        self.assertFalse(engine._running)

    def test_config_wake_word(self):
        """Config'deki wake_word degeri kullanilmali."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy", "wake_word": "test"})
        self.assertEqual(engine.config.get("wake_word"), "test")
        stats = engine.get_stats()
        self.assertEqual(stats["wake_word"], "test")

    def test_start_stop(self):
        """start/stop calismali."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy"})
        result = engine.start()
        self.assertTrue(result)
        self.assertTrue(engine._running)
        self.assertTrue(engine.is_active())
        engine.stop()
        self.assertFalse(engine._running)
        self.assertFalse(engine.is_active())

    def test_start_idempotent(self):
        """start() zaten calisiyorken True donmeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy"})
        engine.start()
        self.assertTrue(engine.start())
        engine.stop()

    def test_feed_audio_not_running(self):
        """feed_audio() calismiyorken None donmeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy"})
        result = engine.feed_audio(b"\x00" * 960)
        self.assertIsNone(result)

    def test_feed_audio_energy_mod(self):
        """feed_audio() energy modunda calisabilmeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={
            "engine": "energy",
            "energy": {"threshold": 0.5, "min_duration_ms": 30, "cooldown_ms": 0},
            "frame_duration_ms": 30,
        })
        engine.start()
        # Dusuk enerji -> None
        result = engine.feed_audio(b"\x00" * 960)
        self.assertIsNone(result)
        engine.stop()

    def test_feed_audio_custom_sample_rate(self):
        """feed_audio() farkli sample_rate ile calisabilmeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={
            "engine": "energy",
            "sample_rate": 48000,
            "energy": {"threshold": 0.5, "min_duration_ms": 30, "cooldown_ms": 0},
            "frame_duration_ms": 30,
        })
        engine.start()
        result = engine.feed_audio(b"\x00" * 2880)
        self.assertIsNone(result)
        engine.stop()

    def test_get_stats(self):
        """get_stats() beklenen anahtarlari icermeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy"})
        stats = engine.get_stats()
        self.assertIn("engine", stats)
        self.assertIn("running", stats)
        self.assertIn("wake_word", stats)

    def test_on_wake_word_callback(self):
        """on_wake_word callback atanabilmeli."""
        from core.wake_word import WakeWordEngine
        fired = []
        engine = WakeWordEngine(
            config={"engine": "energy"},
            on_wake_word=lambda kw: fired.append(kw),
        )
        self.assertIsNotNone(engine.on_wake_word)

    def test_on_error_callback(self):
        """on_error callback atanabilmeli."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(
            config={"engine": "energy"},
            on_error=lambda e: None,
        )
        self.assertIsNotNone(engine.on_error)

    def test_custom_config_override(self):
        """Config dict ile varsayilan degerler ezilebilmeli."""
        from core.wake_word import WakeWordEngine
        cfg = {
            "engine": "energy",
            "wake_word": "computer",
            "sample_rate": 48000,
            "energy": {"threshold": 0.1, "min_duration_ms": 100},
        }
        engine = WakeWordEngine(config=cfg)
        self.assertEqual(engine.config["wake_word"], "computer")
        self.assertEqual(engine.sample_rate, 48000)

    def test_double_stop(self):
        """Ard arda stop hata firlatmamali."""
        from core.wake_word import WakeWordEngine
        engine = WakeWordEngine(config={"engine": "energy"})
        engine.start()
        engine.stop()
        try:
            engine.stop()
        except Exception:
            self.fail("ikinci stop hata firlatti")


class TestCreateWakeWordEngine(unittest.TestCase):
    """Factory fonksiyon testleri."""

    def test_factory_returns_engine(self):
        """create_wake_word_engine WakeWordEngine dondurmeli."""
        from core.wake_word import create_wake_word_engine
        engine = create_wake_word_engine(config={"engine": "energy"})
        self.assertIsNotNone(engine)

    def test_factory_with_callbacks(self):
        """create_wake_word_engine callback'ler ile calisabilmeli."""
        from core.wake_word import create_wake_word_engine
        engine = create_wake_word_engine(
            on_wake_word=lambda kw: None,
            on_error=lambda e: None,
            config={"engine": "energy"},
        )
        self.assertIsNotNone(engine.on_wake_word)
        self.assertIsNotNone(engine.on_error)

    def test_energy_detect_high_energy(self):
        """Yuksek enerjili audio feed_audio keyword dondurebilir."""
        from core.wake_word import WakeWordEngine
        import struct
        engine = WakeWordEngine(config={
            "engine": "energy",
            "wake_word": "jarvis",
            "energy": {"threshold": 0.01, "min_duration_ms": 30, "cooldown_ms": 0},
            "frame_duration_ms": 30,
            "sample_rate": 16000,
        })
        engine.start()
        # 3 frame yuksek enerji gonder
        samples = [30000 if i % 2 == 0 else -30000 for i in range(480)]
        pcm = struct.pack("<" + "h" * 480, *samples)
        for _ in range(3):
            result = engine.feed_audio(pcm)
        engine.stop()
        # 3 frame'den sonra energy detection tetiklenebilir
        # Not: _energy_buffer 3 frame dolunca ve threshold asinca keyword doner
        # RMS / 32768.0 > 0.01 olmali
        # RMS of [30000, -30000, ...] = 30000, normalized = 30000/32768 ≈ 0.915
        # 0.915 > 0.01 ✓


if __name__ == "__main__":
    unittest.main(verbosity=2)
