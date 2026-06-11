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


class TestWeather(unittest.TestCase):
    """weather modulu testleri — API cagrisi yok, hata yolu test edilir."""

    def setUp(self):
        from actions import weather
        self.mod = weather

    def test_get_weather_summary_empty_location(self):
        """get_weather_summary bos konumla calisir (varsayilan Istanbul)."""
        result = self.mod.get_weather_summary(None)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_get_weather_summary_invalid_location(self):
        """get_weather_summary gecersiz konumda hata mesaji doner."""
        result = self.mod.get_weather_summary("xyz_bogus_city_12345")
        self.assertIsInstance(result, str)


# =============================================================================
# 12. OPEN_APP — SAF FONKSIYON TESTLERI
# =============================================================================
