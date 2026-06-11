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


class TestHealthPureFunctions(unittest.TestCase):
    """health pure fonksiyon testleri — dosya okuma yok."""

    def setUp(self):
        from actions import health
        self.mod = health

    def test_normalize_query(self):
        """_normalize_query Turkce karakterleri ascii'ye cevirir."""
        self.assertEqual(self.mod._normalize_query("Nabız ölçümü"), "nabiz olcumu")
        self.assertEqual(self.mod._normalize_query("YÜRÜYÜŞ"), "yuruyus")
        self.assertEqual(self.mod._normalize_query("  Boşluk  "), "bosluk")

    def test_normalize_query_empty(self):
        """_normalize_query bos string calisir."""
        self.assertEqual(self.mod._normalize_query(""), "")
        self.assertEqual(self.mod._normalize_query(None), "")

    def test_extract_target_date_today(self):
        """_extract_target_date 'bugun' bugunun tarihini doner."""
        from datetime import date
        result = self.mod._extract_target_date("bugun")
        self.assertEqual(result, date.today())

    def test_extract_target_date_yesterday(self):
        """_extract_target_date 'dun' dunun tarihini doner."""
        from datetime import date, timedelta
        result = self.mod._extract_target_date("dun")
        self.assertEqual(result, date.today() - timedelta(days=1))

    def test_extract_target_date_iso(self):
        """_extract_target_date ISO formatini cozer."""
        result = self.mod._extract_target_date("2026-06-06")
        from datetime import date
        self.assertEqual(result, date(2026, 6, 6))

    def test_extract_target_date_none(self):
        """_extract_target_date anlamsiz sorgu icin None doner."""
        self.assertIsNone(self.mod._extract_target_date("merhaba dunya"))

    def test_v_formats_values(self):
        """_v degerleri dogru formata cevirir."""
        self.assertEqual(self.mod._v({"x": 72}, "x", " bpm"), "72 bpm")
        self.assertEqual(self.mod._v({"x": 72.5}, "x", " ms", 1), "72.5 ms")
        self.assertEqual(self.mod._v({"x": None}, "x"), "—")
        self.assertEqual(self.mod._v({}, "x"), "—")

    def test_age_str(self):
        """_age_str zaman damgasindan metin uretir."""
        import time
        # 'az once' icin 1 saniye once
        self.assertIn("önce", self.mod._age_str(time.time() - 1))
        # cok eski
        self.assertIn("gün", self.mod._age_str(time.time() - 200000))

    def test_date_from_file_match(self):
        """_date_from_file dosya adindan tarih cikarir."""
        dummy = Path("/fake/HealthAutoExport-2026-06-06.json")
        from datetime import date
        self.assertEqual(self.mod._date_from_file(dummy), date(2026, 6, 6))

    def test_date_from_file_no_match(self):
        """_date_from_file eslesmezse None doner."""
        dummy = Path("/fake/random_file.json")
        self.assertIsNone(self.mod._date_from_file(dummy))
        self.assertIsNone(self.mod._date_from_file(None))

    def test_get_health_data_no_file(self):
        """get_health_data dosya yokken hata mesaji doner."""
        result = self.mod.get_health_data("all")
        # Dosya olmadiginda "bulunamadi" mesaji donmeli
        self.assertIn("bulunamadı", result.lower())

    def test_get_welcome_health_summary_no_file(self):
        """get_welcome_health_summary dosya yokken hata mesaji doner."""
        result = self.mod.get_welcome_health_summary()
        self.assertIn("alınamadı", result.lower())


# =============================================================================
# 7. SISTEM BILGISI (sys_info) — SAF FONKSIYON TESTLERI
# =============================================================================
