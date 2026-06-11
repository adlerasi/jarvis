from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

try:
    import pyaudio  # noqa: F401
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    from google import genai  # noqa: F401
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestMainPureFunctions(unittest.TestCase):
    """main.py statik fonksiyon testleri — Gemini/PyAudio baglantisi yok."""

    @classmethod
    def setUpClass(cls):
        try:
            from main import JarvisLive, load_system_prompt
            cls.JarvisLive = JarvisLive
            cls.load_system_prompt = load_system_prompt
            cls.main_available = True
        except ImportError:
            cls.main_available = False

    def setUp(self):
        if not self.main_available:
            self.skipTest("main.py import edilemedi (pyaudio veya google-genai eksik)")

    def test_load_system_prompt(self):
        """load_system_prompt() prompt.txt'yi okur."""
        from main import load_system_prompt as fn
        result = fn()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 100)

    def test_clean_transcript_text(self):
        """clean_transcript_text metni temizler (case korunur)."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("Merhaba dunya")
        self.assertEqual(text, "Merhaba dunya")
        self.assertFalse(had_noise)

    def test_clean_transcript_text_removes_control(self):
        """clean_transcript_text kontrol token'larini temizler."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("<ctrl123> Merhaba")
        self.assertEqual(text, "Merhaba")
        self.assertTrue(had_noise)

    def test_result_looks_like_error_positive(self):
        """_result_looks_like_error hata metnini tanir."""
        self.assertTrue(self.JarvisLive._result_looks_like_error("hata: dosya bulunamadi"))
        self.assertTrue(self.JarvisLive._result_looks_like_error("Error: connection failed"))

    def test_result_looks_like_error_empty(self):
        """_result_looks_like_error bos string icin False doner (hata yok)."""
        self.assertFalse(self.JarvisLive._result_looks_like_error(""))
        self.assertFalse(self.JarvisLive._result_looks_like_error(None))

    def test_result_looks_like_error_negative(self):
        """_result_looks_like_error normal metni hata olarak algilamaz."""
        self.assertFalse(self.JarvisLive._result_looks_like_error("Islem basariyla tamamlandi"))

    def test_should_play_success_sfx_action_tools(self):
        """_should_play_success_sfx action tool'lari icin True doner."""
        self.assertTrue(self.JarvisLive._should_play_success_sfx("open_app", {}, ""))
        self.assertTrue(self.JarvisLive._should_play_success_sfx("add_calendar_event", {}, ""))
        self.assertTrue(self.JarvisLive._should_play_success_sfx("add_reminder", {}, ""))
        self.assertTrue(self.JarvisLive._should_play_success_sfx("delete_calendar_event", {}, ""))

    def test_should_play_success_sfx_other(self):
        """_should_play_success_sfx diger araclar icin False doner."""
        self.assertFalse(self.JarvisLive._should_play_success_sfx("get_weather", {}, ""))


# =============================================================================
# 9. TTS — SAF FONKSIYON TESTLERI
# =============================================================================


class TestMainPureFunctionsExtended(unittest.TestCase):
    """main.py ek pure fonksiyon testleri (yuk testi olmadan)."""

    def setUp(self):
        skip = False
        try:
            import main
            self.main = main
        except (ImportError, OSError):
            skip = True
        if skip:
            self.skipTest("main import edilemedi")

    def test_main_module_has_constants(self):
        """main.py gerekli sabitleri iceriyor."""
        for const in ("BASE_DIR", "LOG_DIR", "LOG_FILE", "PROMPT_PATH"):
            self.assertTrue(hasattr(self.main, const), f"{const} eksik")


# =============================================================================
# 21. UI — MODUL SEVIYESI + STATIC METHOD TESTLERI
# =============================================================================
