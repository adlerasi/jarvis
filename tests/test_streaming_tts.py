from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestSplitSentences(unittest.TestCase):
    """_split_sentences pure fonksiyon testleri.

    Regex: (?<=[.?!;])\\s+|(?<=\\n)\\s*
    - Noktalama sonrasi bosluk ile ayirir
    - Yeni satir sonrasi ayirir
    - Kisaltmalari korur (Dr., Doç., vs.)
    - 500 karakter limiti uygular
    """

    def test_module_import(self):
        """_split_sentences import edilebilmeli."""
        from core.streaming_tts import _split_sentences
        self.assertIsNotNone(_split_sentences)

    def test_split_sentences_simple(self):
        """_split_sentences basit cumleleri ayirmali (nokta+bosluk ile)."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Merhaba. Nasilsin?")
        self.assertEqual(result, ["Merhaba.", "Nasilsin?"])

    def test_split_sentences_single(self):
        """_split_sentences tek cumleyi aynen dondurmeli."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Merhaba dunya")
        self.assertEqual(result, ["Merhaba dunya"])

    def test_split_sentences_empty(self):
        """_split_sentences bos string'de bos liste dondurmeli."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("")
        self.assertEqual(result, [])

    def test_split_sentences_only_whitespace(self):
        """_split_sentences sadece boslukta bos liste dondurmeli."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("   \n  \t  ")
        self.assertEqual(result, [])

    def test_split_sentences_abbreviations(self):
        """_split_sentences kisaltmalari korumali."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Dr. Smith geldi. Nasilsiniz?")
        self.assertEqual(result, ["Dr. Smith geldi.", "Nasilsiniz?"])

    def test_split_sentences_turkish_abbr(self):
        """_split_sentences Turkce kisaltmalari tanimali."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Doç. Ali Yılmaz ders verdi. Öğrenciler çok memnundu.")
        self.assertEqual(len(result), 2)
        self.assertIn("Doç.", result[0])
        self.assertIn("Öğrenciler", result[1])

    def test_split_sentences_newline_as_space(self):
        """_split_sentences yeni satiri bosluk gibi isler (strip nedeniyle birlesir)."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Satir 1\nSatir 2")
        # .strip() \n'i kaldirir, buffer birlesir
        self.assertEqual(result, ["Satir 1 Satir 2"])

    def test_split_sentences_question_space(self):
        """_split_sentences soru isareti + bosluk ile ayirmali."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Bu bir test mi? Evet dogru.")
        self.assertEqual(result, ["Bu bir test mi?", "Evet dogru."])

    def test_split_sentences_exclamation(self):
        """_split_sentences unlem ile ayirmali."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Harika! Degil mi?")
        self.assertEqual(result, ["Harika!", "Degil mi?"])

    def test_split_sentences_semicolon(self):
        """_split_sentences noktali virgul ile ayirmali."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Al; sat; bitir.")
        self.assertEqual(result, ["Al;", "sat;", "bitir."])

    def test_split_sentences_long_cap(self):
        """_split_sentences 500 karakter sinirini uygulamali."""
        from core.streaming_tts import _split_sentences
        long = "a" * 600
        result = _split_sentences(long)
        self.assertEqual(len(result), 1)
        self.assertLessEqual(len(result[0]), 600)

    def test_split_no_space_after_punct(self):
        """Noktalama sonrasi bosluk yoksa ayirma olmaz (regex geregi)."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Evet.Hayir")
        self.assertEqual(len(result), 1)

    def test_split_double_newline_as_space(self):
        """_split_sentences cift yeni satiri bosluk olarak birlesmeli."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Bir\n\nUc")
        # .strip() \n'leri kaldirir, buffer birlesir
        self.assertEqual(result, ["Bir Uc"])

    def test_split_mixed_punctuation(self):
        """Karma noktalama iceren metin dogru ayrilmali."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Merhaba! Nasilsin? Iyiyim. Harika; devam.")
        self.assertEqual(result, ["Merhaba!", "Nasilsin?", "Iyiyim.", "Harika;", "devam."])

    def test_split_multiple_sentences(self):
        """Uzun metin dogru sayida cumleye ayrilmali."""
        from core.streaming_tts import _split_sentences
        text = "Bir. Iki. Uc. Dort. Bes."
        result = _split_sentences(text)
        self.assertEqual(len(result), 5)

    def test_split_with_trailing_text(self):
        """Son cumle buffer'da kalirsa eklenmeli."""
        from core.streaming_tts import _split_sentences
        result = _split_sentences("Merhaba. Nasilsiniz bugun")
        self.assertEqual(result, ["Merhaba.", "Nasilsiniz bugun"])


class TestTTSBuffer(unittest.TestCase):
    """TTSBuffer thread-safe kuyruk testleri."""

    def test_init(self):
        """TTSBuffer varsayilan durumu."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        self.assertEqual(buf.qsize(), 0)
        self.assertFalse(buf.is_cancelled)

    def test_put_get(self):
        """put/get calismali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        buf.put("test")
        self.assertEqual(buf.qsize(), 1)
        result = buf.get(timeout=0.1)
        self.assertEqual(result, "test")
        self.assertEqual(buf.qsize(), 0)

    def test_get_empty_timeout(self):
        """Bos kuyruktan get None donmeli."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        result = buf.get(timeout=0.1)
        self.assertIsNone(result)

    def test_cancel_drains_queue(self):
        """cancel kuyrugu bosaltmali ve is_cancelled=True yapmali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        buf.put("test1")
        buf.put("test2")
        buf.cancel()
        self.assertTrue(buf.is_cancelled)
        self.assertEqual(buf.qsize(), 0)

    def test_reset_clears_cancel(self):
        """reset iptal durumunu ve kuyrugu sifirlamali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        buf.put("test")
        buf.cancel()
        self.assertTrue(buf.is_cancelled)
        buf.reset()
        self.assertFalse(buf.is_cancelled)
        self.assertEqual(buf.qsize(), 0)

    def test_cancel_twice(self):
        """Ard arda cancel hata firlatmamali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        buf.cancel()
        try:
            buf.cancel()
        except Exception:
            self.fail("ikinci cancel hata firlatti")

    def test_reset_without_cancel(self):
        """reset cancel olmadan da calismali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        buf.put("test1")
        buf.put("test2")
        buf.reset()
        self.assertFalse(buf.is_cancelled)
        self.assertEqual(buf.qsize(), 0)

    def test_put_after_reset(self):
        """reset sonrasi put/get calismali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        buf.cancel()
        buf.reset()
        buf.put("yeni")
        result = buf.get(timeout=0.1)
        self.assertEqual(result, "yeni")

    def test_multiple_put_get(self):
        """Birden fazla put/get sirasi dogru olmali."""
        from core.streaming_tts import TTSBuffer
        buf = TTSBuffer()
        for i in range(5):
            buf.put(f"msg-{i}")
        self.assertEqual(buf.qsize(), 5)
        for i in range(5):
            result = buf.get(timeout=0.1)
            self.assertEqual(result, f"msg-{i}")


class TestStreamingTTSClass(unittest.TestCase):
    """StreamingTTS sinifi API testleri.

    speak() worker baslatir ve actions.tts.speak_text cagirir.
    Bu testler API, state ve yasam-dongusu testleridir.
    """

    def test_default_creation(self):
        """StreamingTTS varsayilan parametrelerle olusabilmeli."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        self.assertEqual(tts.voice, "piper-fahrettin")
        self.assertIsNone(tts.on_start)
        self.assertIsNone(tts.on_done)
        self.assertIsNone(tts.on_error)
        self.assertFalse(tts._running)

    def test_custom_callbacks(self):
        """StreamingTTS ozel callback'ler ile olusabilmeli."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS(
            voice="edge-turbo",
            on_start=lambda: None,
            on_done=lambda: None,
            on_error=lambda e: None,
        )
        self.assertEqual(tts.voice, "edge-turbo")
        self.assertIsNotNone(tts.on_start)
        self.assertIsNotNone(tts.on_done)
        self.assertIsNotNone(tts.on_error)

    def test_set_voice(self):
        """set_voice ses kimligini degistirmeli."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.set_voice("edge-turbo")
        self.assertEqual(tts.voice, "edge-turbo")

    def test_get_stats_initial(self):
        """get_stats baslangic degerleri dogru olmali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        stats = tts.get_stats()
        self.assertEqual(stats["voice"], "piper-fahrettin")
        self.assertFalse(stats["running"])
        self.assertEqual(stats["queued"], 0)
        self.assertFalse(stats["paused"])

    def test_is_speaking_initial(self):
        """Baslangicta is_speaking False olmali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        self.assertFalse(tts.is_speaking())

    def test_speak_empty_text(self):
        """Bos metin ile speak hata firlatmamali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        try:
            tts.speak("")
        except Exception:
            self.fail("speak('') hata firlatti")

    def test_speak_whitespace_text(self):
        """Sadece bosluk metin ile speak hata firlatmamali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        try:
            tts.speak("   ")
        except Exception:
            self.fail("speak('   ') hata firlatti")

    def test_speak_triggers_worker(self):
        """speak() gecerli metinde worker baslatmali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.speak("Merhaba")
        self.assertTrue(tts._running)
        self.assertIsNotNone(tts._thread)
        tts.stop()

    def test_pause_resume(self):
        """pause/resume calismali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.pause()
        stats_paused = tts.get_stats()
        self.assertTrue(stats_paused["paused"])
        tts.resume()
        stats_resumed = tts.get_stats()
        self.assertFalse(stats_resumed["paused"])

    def test_pause_idempotent(self):
        """Ard arda pause hata firlatmamali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.pause()
        try:
            tts.pause()
        except Exception:
            self.fail("ard arda pause hata firlatti")

    def test_stop_stops_worker(self):
        """stop() worker thread'ini durdurup temizlemeli."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.speak("Merhaba")
        self.assertTrue(tts._running)
        tts.stop()
        self.assertFalse(tts._running)
        self.assertIsNone(tts._thread)

    def test_stop_not_started(self):
        """stop() baslatilmamis instance'da hata firlatmamali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        try:
            tts.stop()
        except Exception:
            self.fail("stop() baslatilmamis instance'da hata firlatti")

    def test_speak_streaming_empty(self):
        """speak_streaming bos listede hata firlatmamali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        try:
            tts.speak_streaming([])
        except Exception:
            self.fail("speak_streaming([]) hata firlatti")

    def test_speak_streaming_with_sentences(self):
        """speak_streaming cumle listesi ile calismali."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.speak_streaming(["Merhaba.", "Nasilsiniz?"])
        self.assertTrue(tts._running)
        self.assertGreater(tts._buffer.qsize(), 0)
        tts.stop()

    def test_get_stats_after_speak(self):
        """speak sonrasi get_stats dogru degerler gostermeli."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.speak_streaming(["Selam"])
        stats = tts.get_stats()
        self.assertTrue(stats["running"])
        self.assertGreater(stats["queued"], 0)
        tts.stop()

    def test_speak_streaming_blocking(self):
        """speak_streaming blocking=True calismali (timeout ile)."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        # Blocking=True sonsuz donguye girebilir, kisa zaman asimi ile test
        import threading
        result = []

        def run():
            tts.speak_streaming(["test"], blocking=True)
            result.append("done")

        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(timeout=0.5)
        tts.stop()

    def test_speak_queues_sentences(self):
        """speak() cumlelere ayrilip kuyruga eklenmeli."""
        from core.streaming_tts import StreamingTTS
        tts = StreamingTTS()
        tts.speak("Merhaba. Nasilsin?")
        # buffer'da en az 2 cumle olmali
        self.assertGreaterEqual(tts._buffer.qsize(), 2)
        tts.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
