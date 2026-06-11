from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestStreamingSTT(unittest.TestCase):
    """StreamingSTT modul import, config ve API testleri.

    Not: faster-whisper kurulu oldugu icin load_model() basarili olur.
    """

    def test_module_import(self):
        """core.streaming_stt import edilebilmeli."""
        from core.streaming_stt import StreamingSTT, RealtimeSTT, create_streaming_stt
        self.assertIsNotNone(StreamingSTT)
        self.assertIsNotNone(RealtimeSTT)
        self.assertIsNotNone(create_streaming_stt)

    def test_default_params(self):
        """Varsayilan parametreler dogru olmali."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        self.assertEqual(stt.device, "cpu")
        self.assertEqual(stt.compute_type, "int8")
        self.assertEqual(stt.language, "tr")
        self.assertEqual(stt.beam_size, 1)
        self.assertEqual(stt.best_of, 1)
        self.assertEqual(stt.temperature, 0.0)
        self.assertFalse(stt.condition_on_previous_text)
        self.assertTrue(stt.vad_filter)
        self.assertEqual(stt.vad_threshold, 0.3)
        self.assertEqual(stt.min_speech_duration_ms, 300)
        self.assertEqual(stt.min_silence_duration_ms, 500)
        self.assertIsNone(stt.model_path)

    def test_initial_state(self):
        """Baslangic durumu dogru olmali."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        self.assertIsNone(stt._model)
        self.assertFalse(stt._model_loaded)
        self.assertFalse(stt._running)
        self.assertEqual(stt.get_current_text(), "")
        self.assertEqual(stt.get_final_text(), "")
        self.assertEqual(stt._transcription_count, 0)
        self.assertEqual(stt._total_audio_processed, 0)

    def test_clear_resets_state(self):
        """clear() text ve buffer'lari sifirlamali."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        stt._current_text = "test"
        stt._final_text = "test final"
        stt._speech_buffer = bytearray(b"testdata")
        stt.clear()
        self.assertEqual(stt.get_current_text(), "")
        self.assertEqual(stt.get_final_text(), "")
        self.assertEqual(len(stt._speech_buffer), 0)

    def test_feed_audio_not_running(self):
        """feed_audio() calismiyorken audio kuyruga eklenmemeli."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        stt.feed_audio(b"test_audio_data")
        self.assertTrue(stt._audio_queue.empty())

    def test_feed_audio_when_running(self):
        """feed_audio() calisirken kuyruga eklenmeli."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        stt._running = True
        stt.feed_audio(b"test_audio_data")
        self.assertFalse(stt._audio_queue.empty())
        self.assertEqual(stt._audio_queue.get_nowait(), b"test_audio_data")

    def test_get_stats_initial(self):
        """get_stats() baslangic degerleri dogru olmali."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        stats = stt.get_stats()
        self.assertFalse(stats["model_loaded"])
        self.assertFalse(stats["running"])
        self.assertEqual(stats["transcription_count"], 0)
        self.assertEqual(stats["last_transcription_time"], 0.0)
        self.assertEqual(stats["total_audio_processed_mb"], 0.0)
        self.assertEqual(stats["buffer_size"], 0)

    def test_load_model_success(self):
        """faster-whisper kurulu oldugunda load_model() True donmeli."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        result = stt.load_model()
        self.assertTrue(result)
        self.assertTrue(stt._model_loaded)
        self.assertIsNotNone(stt._model)
        stt.stop()

    def test_load_model_idempotent(self):
        """load_model() ikinci kez cagrildiginda da True donmeli."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        r1 = stt.load_model()
        r2 = stt.load_model()
        self.assertTrue(r1)
        self.assertTrue(r2)
        stt.stop()

    def test_start_and_stop(self):
        """start() basarili olmali, stop() hata firlatmamali."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        result = stt.start()
        self.assertTrue(result)
        self.assertTrue(stt._running)
        self.assertIsNotNone(stt._thread)
        stt.stop()
        self.assertFalse(stt._running)

    def test_stop_not_started(self):
        """stop() baslatilmamis instance'da hata firlatmamali."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT()
        try:
            stt.stop()
        except Exception:
            self.fail("stop() baslatilmamis instance'da hata firlatti")

    def test_process_audio_chunk_buffer_grows(self):
        """_process_audio_chunk buffer'a data eklemeli."""
        from core.streaming_stt import StreamingSTT
        import numpy as np
        stt = StreamingSTT()
        dummy = np.zeros(3200, dtype=np.int16).tobytes()
        initial_len = len(stt._speech_buffer)
        stt._process_audio_chunk(dummy)
        self.assertGreater(len(stt._speech_buffer), initial_len)

    def test_custom_callbacks(self):
        """StreamingSTT ozel callback'ler ile olusabilmeli."""
        from core.streaming_stt import StreamingSTT
        results = []
        stt = StreamingSTT(
            on_transcription=lambda text, is_final: results.append((text, is_final)),
            on_partial=lambda text: results.append(("partial", text)),
        )
        self.assertIsNotNone(stt.on_transcription)
        self.assertIsNotNone(stt.on_partial)

    def test_custom_vad_params(self):
        """StreamingSTT ozel VAD parametreleri ile olusabilmeli."""
        from core.streaming_stt import StreamingSTT
        stt = StreamingSTT(
            vad_threshold=0.5,
            min_speech_duration_ms=500,
            min_silence_duration_ms=1000,
        )
        self.assertEqual(stt.vad_threshold, 0.5)
        self.assertEqual(stt.min_speech_duration_ms, 500)
        self.assertEqual(stt.min_silence_duration_ms, 1000)


class TestRealtimeSTT(unittest.TestCase):
    """RealtimeSTT wrapper testleri."""

    def test_module_import(self):
        """RealtimeSTT import edilebilmeli."""
        from core.streaming_stt import RealtimeSTT
        self.assertIsNotNone(RealtimeSTT)

    def test_default_creation(self):
        """Varsayilan parametrelerle RealtimeSTT olusturulabilmeli."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        self.assertIsNotNone(r.stt)
        self.assertEqual(r.sample_rate, 16000)
        self.assertEqual(r.chunk_duration_ms, 100)
        self.assertIsNone(r.on_text)

    def test_initial_text_empty(self):
        """Baslangicta text bos olmali."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        self.assertEqual(r.get_text(), "")
        self.assertEqual(r._partial_text, "")
        self.assertEqual(r._final_text, "")

    def test_start_stop(self):
        """start/stop hata firlatmamali."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        result = r.start()
        self.assertTrue(result)
        try:
            r.stop()
        except Exception:
            self.fail("stop hata firlatti")

    def test_clear(self):
        """clear() text temizlemeli."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        r._final_text = "test"
        r._partial_text = "partial"
        r.clear()
        self.assertEqual(r.get_text(), "")
        self.assertEqual(r._partial_text, "")
        self.assertEqual(r._final_text, "")

    def test_feed_chunk(self):
        """feed_chunk hata firlatmamali."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        try:
            r.feed_chunk(b"test")
        except Exception:
            self.fail("feed_chunk hata firlatti")

    def test_stop_twice(self):
        """Ard arda stop hata firlatmamali."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        r.start()
        r.stop()
        try:
            r.stop()
        except Exception:
            self.fail("ikinci stop hata firlatti")

    def test_get_text_after_clear(self):
        """clear sonrasi get_text bos olmali."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT()
        r._final_text = "birikmis metin"
        r.clear()
        self.assertEqual(r.get_text(), "")

    def test_realtimestt_custom_model_path(self):
        """RealtimeSTT ozel model_path ile olusabilmeli."""
        from core.streaming_stt import RealtimeSTT
        r = RealtimeSTT(model_path="base")
        self.assertIsNotNone(r.stt)
        self.assertEqual(r.stt.model_path, "base")


class TestCreateStreamingSTT(unittest.TestCase):
    """Factory fonksiyon testleri."""

    def test_factory_returns_realtimestt(self):
        """create_streaming_stt RealtimeSTT dondurmeli."""
        from core.streaming_stt import RealtimeSTT, create_streaming_stt
        result = create_streaming_stt()
        self.assertIsInstance(result, RealtimeSTT)

    def test_factory_with_on_text(self):
        """create_streaming_stt on_text callback ile calisabilmeli."""
        from core.streaming_stt import create_streaming_stt
        calls = []

        def cb(text: str):
            calls.append(text)

        result = create_streaming_stt(on_text=cb)
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.on_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
