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


class TestSysInfo(unittest.TestCase):
    """sys_info pure fonksiyon testleri."""

    def setUp(self):
        from actions.sys_info import sys_info
        self.func = sys_info

    def test_sys_info_returns_string(self):
        """sys_info() string doner."""
        result = self.func("time")
        self.assertIsInstance(result, str)

    def test_sys_info_unknown_query(self):
        """sys_info bilinmeyen sorguda yardim metni doner."""
        result = self.func("bilinmeyen_sorgu")
        self.assertIn("kullanin", result.lower())

    def test_sys_info_time(self):
        """sys_info('time') saat bilgisi icerir."""
        result = self.func("time")
        self.assertIn("Saat", result)

    def test_sys_info_date(self):
        """sys_info('date') tarih bilgisi icerir."""
        result = self.func("date")
        self.assertIn("Tarih", result)


# =============================================================================
# 8. ANA MODUL (main.py) — SAF FONKSIYON TESTLERI
# =============================================================================
