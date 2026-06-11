from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent


class TestVADEngine(unittest.TestCase):
    """VADEngine import, config ve API testleri.

    Backend chain: silero (PyTorch) -> webrtc (webrtcvad) -> energy (numpy).
    Ortamda PyTorch/webrtcvad yoksa otomatik energy'e duser.
    """

    def test_module_import(self):
        """core.vad_engine import edilebilmeli."""
        from core.vad_engine import VADEngine
        self.assertIsNotNone(VADEngine)

    def test_default_creation(self):
        """VADEngine varsayilan parametrelerle olusabilmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        self.assertEqual(engine.sample_rate, 16000)
        self.assertEqual(engine.frame_duration_ms, 30)
        self.assertEqual(engine.aggressiveness, 2)
        self.assertIn(engine.engine_name, ("silero", "webrtc", "energy"))
        self.assertIsNotNone(engine._engine)

    def test_force_energy_engine(self):
        """engine='energy' ile dogrudan energy VAD kullanilabilmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine(engine="energy")
        self.assertEqual(engine.engine_name, "energy")
        self.assertEqual(engine._engine, "energy")

    def test_custom_threshold(self):
        """VADEngine custom energy_threshold ile olusabilmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine(energy_threshold=80.0)
        self.assertEqual(engine.energy_threshold, 80.0)

    def test_default_energy_threshold(self):
        """Varsayilan energy_threshold 50.0 olmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        self.assertEqual(engine.energy_threshold, 50.0)

    def test_frame_duration_10ms(self):
        """10ms frame_duration_ms ile olusabilmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine(frame_duration_ms=10)
        self.assertEqual(engine.frame_duration_ms, 10)

    def test_frame_duration_20ms(self):
        """20ms frame_duration_ms ile olusabilmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine(frame_duration_ms=20)
        self.assertEqual(engine.frame_duration_ms, 20)

    def test_process_frame_energy(self):
        """process_frame energy modunda calismali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(engine="energy")
        is_speech, confidence = engine.process_frame(b"\x00" * 960, sample_rate=16000)
        self.assertIsInstance(is_speech, (bool, np.bool_))
        self.assertIsInstance(confidence, float)

    def test_process_frame_silence(self):
        """Sessizlik False donmeli."""
        from core.vad_engine import VADEngine
        import numpy as np
        engine = VADEngine(engine="energy", energy_threshold=10.0)
        is_speech, confidence = engine.process_frame(b"\x00" * 960, sample_rate=16000)
        self.assertFalse(is_speech)

    def test_process_frame_high_energy(self):
        """Yuksek RMS'li frame True donmeli."""
        from core.vad_engine import VADEngine
        import struct
        engine = VADEngine(engine="energy", energy_threshold=5.0)
        samples = [8000 if i % 2 == 0 else -8000 for i in range(480)]
        pcm = struct.pack("<" + "h" * 480, *samples)
        is_speech, confidence = engine.process_frame(pcm, sample_rate=16000)
        self.assertTrue(is_speech)

    def test_process_frame_48khz_downsample(self):
        """48kHz -> 16kHz downsampling ile process_frame calismali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(engine="energy")
        is_speech, confidence = engine.process_frame(b"\x00" * 2880, sample_rate=48000)
        self.assertIsInstance(is_speech, (bool, np.bool_))

    def test_process_frame_44khz_downsample(self):
        """44.1kHz -> 16kHz downsampling ile process_frame calismali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(engine="energy")
        is_speech, confidence = engine.process_frame(b"\x00" * 2646, sample_rate=44100)
        self.assertIsInstance(is_speech, (bool, np.bool_))

    def test_is_speaking_initial(self):
        """Baslangicta is_speaking False olmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        self.assertFalse(engine.is_speaking())

    def test_reset(self):
        """reset hata firlatmamali ve state sifirlanmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        engine.reset()
        self.assertFalse(engine._is_speaking)
        self.assertIsNone(engine._speech_start_time)
        self.assertIsNone(engine._last_speech_time)
        self.assertIsNone(engine._silence_start_time)
        self.assertEqual(len(engine._audio_buffer), 0)
        self.assertEqual(len(engine._speech_buffer), 0)

    def test_get_stats(self):
        """get_stats beklenen anahtarlari icermeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        stats = engine.get_stats()
        self.assertIn("engine", stats)
        self.assertIn("is_speaking", stats)
        self.assertIn("speech_count", stats)
        self.assertIn("total_frames", stats)
        self.assertIn("noise_floor", stats)
        self.assertIn("buffer_size", stats)

    def test_get_speech_segment_empty(self):
        """Konusma yokken get_speech_segment None donmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        segment = engine.get_speech_segment()
        self.assertIsNone(segment)

    def test_process_stream_basic(self):
        """process_stream hata firlatmamali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(engine="energy")
        result = engine.process_stream(b"\x00" * 9600)
        self.assertIsNone(result)

    def test_on_speech_start_end_callbacks(self):
        """on_speech_start/on_speech_end callback'leri atanabilmeli."""
        from core.vad_engine import VADEngine
        engine = VADEngine(
            engine="energy",
            on_speech_start=lambda: None,
            on_speech_end=lambda: None,
        )
        self.assertIsNotNone(engine.on_speech_start)
        self.assertIsNotNone(engine.on_speech_end)

    def test_custom_aggressiveness(self):
        """aggressiveness parametresi dogru atanmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(aggressiveness=3)
        self.assertEqual(engine.aggressiveness, 3)

    def test_speech_pad_ms(self):
        """speech_pad_ms parametresi dogru atanmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(speech_pad_ms=500)
        self.assertEqual(engine.speech_pad_ms, 500)

    def test_min_speech_duration(self):
        """min_speech_duration_ms parametresi dogru atanmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(min_speech_duration_ms=100)
        self.assertEqual(engine.min_speech_duration_ms, 100)

    def test_min_silence_duration(self):
        """min_silence_duration_ms parametresi dogru atanmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(min_silence_duration_ms=200)
        self.assertEqual(engine.min_silence_duration_ms, 200)

    def test_noise_profile_initial(self):
        """Baslangicta noise_floor None olmali."""
        from core.vad_engine import VADEngine
        engine = VADEngine(engine="energy")
        self.assertIsNone(engine._noise_floor)

    def test_multiple_instances(self):
        """Birden fazla VADEngine instance'i sorunsuz calismali."""
        from core.vad_engine import VADEngine
        e1 = VADEngine(engine="energy")
        e2 = VADEngine(engine="energy", energy_threshold=30.0)
        e3 = VADEngine(engine="energy", frame_duration_ms=20)
        self.assertIsNotNone(e1)
        self.assertIsNotNone(e2)
        self.assertIsNotNone(e3)
        self.assertFalse(e1.is_speaking())
        self.assertFalse(e2.is_speaking())
        self.assertFalse(e3.is_speaking())

    def test_frame_size_calculation(self):
        """frame_size dogru hesaplanmali (30ms @ 16kHz = 480)."""
        from core.vad_engine import VADEngine
        engine = VADEngine()
        self.assertEqual(engine.frame_size, 480)

    def test_frame_size_10ms(self):
        """frame_size 10ms @ 16kHz = 160."""
        from core.vad_engine import VADEngine
        engine = VADEngine(frame_duration_ms=10)
        self.assertEqual(engine.frame_size, 160)


class TestCreateVADEngine(unittest.TestCase):
    """Factory fonksiyon testleri."""

    def test_factory_returns_vadengine(self):
        """create_vad_engine VADEngine dondurmeli."""
        from core.vad_engine import create_vad_engine
        engine = create_vad_engine()
        self.assertIsNotNone(engine)

    def test_factory_with_callbacks(self):
        """create_vad_engine callback'ler ile calisabilmeli."""
        from core.vad_engine import create_vad_engine
        engine = create_vad_engine(
            on_speech_start=lambda: None,
            on_speech_end=lambda: None,
        )
        self.assertIsNotNone(engine.on_speech_start)
        self.assertIsNotNone(engine.on_speech_end)

    def test_factory_with_energy_threshold(self):
        """create_vad_engine energy_threshold ile calisabilmeli."""
        from core.vad_engine import create_vad_engine
        engine = create_vad_engine(energy_threshold=25.0)
        self.assertEqual(engine.energy_threshold, 25.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
