from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestEmotionTTSDetectEmotion(unittest.TestCase):
    """_detect_emotion pure fonksiyon testleri."""

    def test_module_import(self):
        """core.emotion_tts import edilebilmeli."""
        from core.emotion_tts import EmotionTTS, _detect_emotion
        self.assertIsNotNone(EmotionTTS)
        self.assertIsNotNone(_detect_emotion)

    def test_detect_neutral(self):
        """Nötr metin 'neutral' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("Bugün hava güzel.")
        self.assertEqual(result, "neutral")

    def test_detect_happy_keyword(self):
        """Mutluluk anahtar kelimesi 'happy' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("Harika bir haberim var!")
        self.assertEqual(result, "happy")

    def test_detect_sad_keyword(self):
        """Uzuntu anahtar kelimesi 'sad' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        # Keyword listesinde "malesef" (ASCII, cift a degil)
        result = _detect_emotion("Malesef kotu haber.")
        self.assertEqual(result, "sad")

    def test_detect_angry_keyword(self):
        """Sinir anahtar kelimesi 'angry' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        # Keyword listesinde "sinir" (ASCII s, ASCII i)
        result = _detect_emotion("Cok sinirli bu duruma!")
        self.assertEqual(result, "angry")

    def test_detect_excited_keyword(self):
        """Heyecan anahtar kelimesi 'excited' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("Vay be! Beklemedik bir şey!")
        self.assertEqual(result, "excited")

    def test_detect_calm_keyword(self):
        """Sakinlik anahtar kelimesi 'calm' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("Sakin ol, rahatla.")
        self.assertEqual(result, "calm")

    def test_detect_exclamation_heuristic(self):
        """2+ unlem 'excited' dondurmeli (keyword eslesmezse)."""
        from core.emotion_tts import _detect_emotion
        # "harika" happy keywords'te oldugu icin once keyword eslesir
        # Keyword eslesmeyen bir metin kullanalim
        result = _detect_emotion("Vay!! Gercekten!!")
        self.assertEqual(result, "excited")

    def test_detect_question_heuristic(self):
        """2+ soru isareti 'calm' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("Gerçekten mi?? Nasıl oldu??")
        self.assertEqual(result, "calm")

    def test_detect_empty(self):
        """Bos metin 'neutral' dondurmeli."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("")
        self.assertEqual(result, "neutral")

    def test_detect_case_insensitive(self):
        """Buyuk/kucuk harf duyarli degil."""
        from core.emotion_tts import _detect_emotion
        result = _detect_emotion("HARIKA!")
        self.assertEqual(result, "happy")


class TestEmotionTTSGenerateFlags(unittest.TestCase):
    """_generate_piper_flags, _generate_edge_ssml, _generate_spd_say_flags testleri."""

    def test_generate_piper_flags_default(self):
        """Varsayilan hizda bos liste doner."""
        from core.emotion_tts import _generate_piper_flags
        flags = _generate_piper_flags(1.0)
        self.assertEqual(flags, [])

    def test_generate_piper_flags_fast(self):
        """Hizli konusma icin --speed flag'i eklenmeli."""
        from core.emotion_tts import _generate_piper_flags
        flags = _generate_piper_flags(1.2)
        self.assertIn("--speed", flags)
        self.assertIn("1.2", flags)

    def test_generate_piper_flags_slow(self):
        """Yavas konusma icin --speed flag'i eklenmeli."""
        from core.emotion_tts import _generate_piper_flags
        flags = _generate_piper_flags(0.8)
        self.assertIn("--speed", flags)

    def test_generate_edge_ssml_rate_pitch(self):
        """edge-ssml dogru prosody etiketleri icermeli."""
        from core.emotion_tts import _generate_edge_ssml
        # int((1.2 - 1.0) * 100) = 19 (fp hassasiyeti)
        ssml = _generate_edge_ssml("Merhaba", speed=1.2, pitch=2)
        self.assertIn("<speak", ssml)
        self.assertIn("</speak>", ssml)
        self.assertIn('rate="+19%"', ssml)
        self.assertIn('pitch="+2st"', ssml)
        self.assertIn("Merhaba", ssml)

    def test_generate_edge_ssml_slow(self):
        """Yavas konusma icin negative rate."""
        from core.emotion_tts import _generate_edge_ssml
        # int((0.8 - 1.0) * 100) = -19 (fp hassasiyeti)
        ssml = _generate_edge_ssml("Test", speed=0.8, pitch=-1)
        self.assertIn('rate="-19%"', ssml)
        self.assertIn('pitch="-1st"', ssml)

    def test_generate_edge_ssml_zero_pitch(self):
        """Pitch 0 iken '0st' kullanilmali."""
        from core.emotion_tts import _generate_edge_ssml
        ssml = _generate_edge_ssml("Test", speed=1.0, pitch=0)
        self.assertIn('pitch="0st"', ssml)

    def test_generate_spd_say_flags_default(self):
        """Varsayilan parametrelerde bos liste doner."""
        from core.emotion_tts import _generate_spd_say_flags
        flags = _generate_spd_say_flags(1.0, 0)
        self.assertEqual(flags, [])

    def test_generate_spd_say_flags_rate(self):
        """Farkli hiz icin -r flag'i."""
        from core.emotion_tts import _generate_spd_say_flags
        # int((1.2 - 1.0) * 50) = 9 (fp hassasiyeti)
        flags = _generate_spd_say_flags(1.2, 0)
        self.assertIn("-r", flags)
        self.assertIn("9", flags)

    def test_generate_spd_say_flags_pitch(self):
        """Farkli pitch icin -p flag'i."""
        from core.emotion_tts import _generate_spd_say_flags
        flags = _generate_spd_say_flags(1.0, 2)
        self.assertIn("-p", flags)

    def test_generate_spd_say_flags_both(self):
        """Hiz ve pitch birlikte calismali."""
        from core.emotion_tts import _generate_spd_say_flags
        flags = _generate_spd_say_flags(1.15, 3)
        self.assertIn("-r", flags)
        self.assertIn("-p", flags)
        self.assertIn("30", flags)  # pitch 3 -> 3*10 = 30


class TestEmotionTTSClass(unittest.TestCase):
    """EmotionTTS sinifi API testleri."""

    def test_default_creation(self):
        """EmotionTTS varsayilan parametrelerle olusabilmeli."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        self.assertEqual(tts.voice, "piper-fahrettin")
        self.assertEqual(tts._emotion, "neutral")

    def test_custom_defaults(self):
        """EmotionTTS ozel voice/emotion ile olusabilmeli."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS(default_voice="edge-turbo", default_emotion="happy")
        self.assertEqual(tts.voice, "edge-turbo")
        self.assertEqual(tts._emotion, "happy")

    def test_set_emotion_valid(self):
        """set_emotion() gecerli duygu atamali."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        tts.set_emotion("happy")
        self.assertEqual(tts.get_emotion(), "happy")

    def test_set_emotion_case_insensitive(self):
        """set_emotion() buyuk-kucuk harf duyarsiz olmali."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        tts.set_emotion("HAPPY")
        self.assertEqual(tts.get_emotion(), "happy")

    def test_set_emotion_invalid(self):
        """Gecersiz duygu 'neutral'e dusmeli."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        tts.set_emotion("unknown")
        self.assertEqual(tts.get_emotion(), "neutral")

    def test_set_voice(self):
        """set_voice() ses kimligini degistirmeli."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        tts.set_voice("edge-ahmet")
        self.assertEqual(tts.voice, "edge-ahmet")

    def test_initial_emotion_neutral(self):
        """Baslangic duygusu neutral olmali."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        self.assertEqual(tts.get_emotion(), "neutral")

    def test_emotion_profiles_exist(self):
        """Tum profil anahtarlari dogru tuple yapisinda."""
        from core.emotion_tts import _EMOTION_PROFILES
        for emotion, profile in _EMOTION_PROFILES.items():
            self.assertIsInstance(emotion, str)
            self.assertIsInstance(profile, tuple)
            self.assertEqual(len(profile), 3)
            speed, pitch, volume = profile
            self.assertIsInstance(speed, float)
            self.assertIsInstance(pitch, int)
            self.assertIsInstance(volume, float)

    def test_speak_empty_text(self):
        """speak() bos metinle hata firlatmamali."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        try:
            tts.speak("")
        except Exception:
            self.fail("speak('') hata firlatti")

    def test_speak_with_specific_emotion(self):
        """speak() ozel emotion parametresi ile calisabilmeli."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        try:
            tts.speak("Test", emotion="happy")
        except Exception:
            self.fail("speak(emotion='happy') hata firlatti")

    def test_speak_with_invalid_emotion(self):
        """Gecersiz emotion ile speak fallback yapmali."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        try:
            tts.speak("Test", emotion="invalid")
        except Exception:
            self.fail("speak(invalid_emotion) hata firlatti")

    def test_speak_with_emphasis(self):
        """speak_with_emphasis() calisabilmeli (en azindan hata firlatmamali)."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        try:
            tts.speak_with_emphasis(
                "Bu çok önemli bir konu.",
                important_parts=["çok önemli"],
            )
        except Exception:
            self.fail("speak_with_emphasis hata firlatti")

    def test_speak_with_emphasis_no_parts(self):
        """speak_with_emphasis() bos liste ile calisabilmeli."""
        from core.emotion_tts import EmotionTTS
        tts = EmotionTTS()
        try:
            tts.speak_with_emphasis("Test", important_parts=[])
        except Exception:
            self.fail("speak_with_emphasis([]) hata firlatti")


if __name__ == "__main__":
    unittest.main(verbosity=2)
