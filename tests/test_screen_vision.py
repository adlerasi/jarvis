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


class TestScreenVision(unittest.TestCase):
    """screen_vision modulu — pure fonksiyon testleri (API cagrisi yok)."""

    def setUp(self):
        from actions import screen_vision
        self.mod = screen_vision

    def test_screen_permission_message(self):
        """_screen_permission_message string doner."""
        result = self.mod._screen_permission_message()
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)

    def test_vision_prompt(self):
        """_vision_prompt prompt metni olusturur."""
        result = self.mod._vision_prompt("Nedir bu?", "Kullanici", "Not Defteri")
        self.assertIn("Nedir bu?", result)
        self.assertIn("Not Defteri", result)
        self.assertIn("Turkce", result)

    def test_vision_prompt_default_query(self):
        """_vision_prompt sorgu yoksa varsayilan kullanir."""
        result = self.mod._vision_prompt("", "Kullanici", "Pencere")
        self.assertIn("Ekranda ne var?", result)

    def test_extract_response_text_with_text(self):
        """_extract_response_text response.text alanini okur."""
        class FakeResponse:
            text = "Merhaba dunya"
            candidates = []
        result = self.mod._extract_response_text(FakeResponse())
        self.assertEqual(result, "Merhaba dunya")

    def test_extract_response_text_with_candidates(self):
        """_extract_response_text candidates icinden text birlestirir."""
        class FakePart:
            text = "birinci"
        class FakeContent:
            parts = [FakePart()]
        class FakeCandidate:
            content = FakeContent()
        class FakeResponse:
            text = ""
            candidates = [FakeCandidate()]
        result = self.mod._extract_response_text(FakeResponse())
        self.assertEqual(result, "birinci")

    def test_extract_response_text_empty(self):
        """_extract_response_text bos yanitta bos string doner."""
        class FakeResponse:
            text = ""
            candidates = []
        result = self.mod._extract_response_text(FakeResponse())
        self.assertEqual(result, "")

    def test_is_transient_vision_error_server_error(self):
        """_is_transient_vision_error ServerError'i gecici kabul eder."""
        from google.genai import errors
        exc = errors.ServerError(code=503, response_json={}, response="Service Unavailable")
        self.assertTrue(self.mod._is_transient_vision_error(exc))

    def test_is_transient_vision_error_timeout(self):
        """_is_transient_vision_error TimeoutError'i gecici kabul eder."""
        self.assertTrue(self.mod._is_transient_vision_error(TimeoutError("timed out")))

    def test_is_transient_vision_error_status_codes(self):
        """_is_transient_vision_error 503/429 kodlarini tanir."""
        self.assertTrue(self.mod._is_transient_vision_error(RuntimeError("503 Service Unavailable")))
        self.assertTrue(self.mod._is_transient_vision_error(RuntimeError("429 Too Many Requests")))

    def test_is_transient_vision_error_other_exception(self):
        """_is_transient_vision_error ilgisiz hatada False."""
        self.assertFalse(self.mod._is_transient_vision_error(ValueError("invalid")))

    def test_friendly_vision_error_quota(self):
        """_friendly_vision_error kota hatasini tanir."""
        result = self.mod._friendly_vision_error(RuntimeError("quota exceeded"))
        self.assertIn("kota", result)

    def test_friendly_vision_error_transient(self):
        """_friendly_vision_error gecici hatayi tanir."""
        result = self.mod._friendly_vision_error(RuntimeError("503 unavailable"))
        self.assertIn("ulasilamiyor", result)

    def test_friendly_vision_error_generic(self):
        """_friendly_vision_error genel hatada hatayi yansitir."""
        result = self.mod._friendly_vision_error(RuntimeError("something broke"))
        self.assertIn("something broke", result)

    def test_analyze_screen_wrong_target(self):
        """analyze_screen gecersiz target icin uyari doner."""
        result = self.mod.analyze_screen("ne var?", target="full_screen")
        self.assertIn("yalnizca", result)


# =============================================================================
# 20. MAIN PURE — KALAN TESTLER TAMAMLANDI
# =============================================================================
