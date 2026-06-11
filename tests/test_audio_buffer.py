from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestAudioBuffer(unittest.TestCase):
    """AudioBuffer ring buffer testleri."""

    def test_module_import(self):
        """core.audio_buffer import edilebilmeli."""
        from core.audio_buffer import AudioBuffer
        self.assertIsNotNone(AudioBuffer)

    def test_default_creation(self):
        """AudioBuffer varsayilan parametrelerle olusabilmeli."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer()
        self.assertEqual(buf.sample_rate, 16000)
        self.assertEqual(len(buf), 0)
        self.assertEqual(buf._total_written, 0)
        self.assertEqual(buf._write_count, 0)

    def test_custom_params(self):
        """AudioBuffer ozel sample_rate ve max_duration ile olusabilmeli."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer(sample_rate=48000, max_duration=60.0)
        self.assertEqual(buf.sample_rate, 48000)
        self.assertEqual(buf._buffer.maxlen, 48000 * 60)

    def test_write_and_len(self):
        """write() buffer boyutunu artirmali."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        data = np.zeros(480, dtype=np.int16).tobytes()
        buf.write(data)
        self.assertEqual(len(buf), 480)
        self.assertEqual(buf._write_count, 1)
        self.assertEqual(buf._total_written, 480)

    def test_write_multiple(self):
        """Ard arda write() dogru calismali."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        for _ in range(5):
            buf.write(np.zeros(480, dtype=np.int16).tobytes())
        self.assertEqual(len(buf), 480 * 5)
        self.assertEqual(buf._write_count, 5)
        self.assertEqual(buf._total_written, 480 * 5)

    def test_read_empty(self):
        """Bos buffer'dan read None donmeli."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer()
        result = buf.read(100)
        self.assertIsNone(result)

    def test_read_basic(self):
        """read() dogru uzunlukta PCM dondurmeli."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        buf.write(np.zeros(16000, dtype=np.int16).tobytes())
        # 100ms @ 16kHz = 1600 samples = 3200 bytes
        result = buf.read(100)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3200)

    def test_read_shorter_than_requested(self):
        """read() buffer'dan kisa ise mevcut kadarini dondurur."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        buf.write(np.zeros(800, dtype=np.int16).tobytes())
        result = buf.read(100)  # 100ms = 1600 sample ister, 800 var
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1600)  # 800 sample = 1600 bytes

    def test_clear(self):
        """clear() buffer'i sifirlamali."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        buf.write(np.zeros(480, dtype=np.int16).tobytes())
        self.assertGreater(len(buf), 0)
        buf.clear()
        self.assertEqual(len(buf), 0)

    def test_ring_buffer_wraps(self):
        """Ring buffer maxlen'dan fazla yazilinca eski veriyi kaybeder."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer(sample_rate=16000, max_duration=0.1)  # 0.1s = 1600 sample
        # 2000 sample yaz (max 1600)
        buf.write(np.zeros(2000, dtype=np.int16).tobytes())
        self.assertLessEqual(len(buf), 1600)

    def test_duration_ms(self):
        """duration_ms dogru hesaplanmali."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer(sample_rate=16000)
        buf.write(np.zeros(16000, dtype=np.int16).tobytes())
        self.assertAlmostEqual(buf.duration_ms, 1000.0, delta=1)

    def test_read_frame(self):
        """read_frame() onden frame cekmeli."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        data = np.array([1, 2, 3, 4, 5], dtype=np.int16).tobytes()
        buf.write(data)
        frame = buf.read_frame(3)
        self.assertIsNotNone(frame)
        self.assertEqual(len(frame), 6)  # 3 samples = 6 bytes
        # Kalan 2 sample
        self.assertEqual(len(buf), 2)

    def test_read_frame_not_enough(self):
        """read_frame() yeterli sample yoksa None doner."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer()
        self.assertIsNone(buf.read_frame(100))

    def test_peek(self):
        """peek() son n sample'i almali ama buffer'dan silmemeli."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        data = np.array([1, 2, 3, 4, 5], dtype=np.int16).tobytes()
        buf.write(data)
        peeked = buf.peek(3)
        self.assertIsNotNone(peeked)
        self.assertEqual(len(peeked), 6)  # 3 samples = 6 bytes
        self.assertEqual(len(buf), 5)  # peek silmez

    def test_peek_empty(self):
        """peek() bos buffer'da None donmeli."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer()
        self.assertIsNone(buf.peek(10))

    def test_peek_negative(self):
        """peek() negatif n_samples'de None donmeli."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer()
        self.assertIsNone(buf.peek(-1))

    def test_get_stats(self):
        """get_stats() beklenen anahtarlari icermeli."""
        from core.audio_buffer import AudioBuffer
        buf = AudioBuffer()
        stats = buf.get_stats()
        self.assertIn("sample_rate", stats)
        self.assertIn("current_samples", stats)
        self.assertIn("current_duration_ms", stats)
        self.assertIn("max_samples", stats)
        self.assertIn("total_written", stats)
        self.assertIn("write_count", stats)
        self.assertIn("age_seconds", stats)

    def test_get_stats_after_write(self):
        """get_stats() yazma sonrasi dogru degerler gostermeli."""
        from core.audio_buffer import AudioBuffer
        import numpy as np
        buf = AudioBuffer()
        buf.write(np.zeros(480, dtype=np.int16).tobytes())
        stats = buf.get_stats()
        self.assertEqual(stats["current_samples"], 480)
        self.assertEqual(stats["total_written"], 480)
        self.assertEqual(stats["write_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
