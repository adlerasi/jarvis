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


class TestOpenApp(unittest.TestCase):
    """open_app modulu — alias dict + validation."""

    def setUp(self):
        from actions.open_app import open_app, APP_ALIASES
        self.open_app = open_app
        self.alias_dict = APP_ALIASES

    def test_app_aliases_is_dict(self):
        """APP_ALIASES dict ve bos degil."""
        self.assertIsInstance(self.alias_dict, dict)
        self.assertGreater(len(self.alias_dict), 0)

    def test_app_aliases_keys_are_strings(self):
        """APP_ALIASES anahtarlarinin hepsi string."""
        for key in self.alias_dict:
            self.assertIsInstance(key, str)

    def test_app_aliases_values_are_strings(self):
        """APP_ALIASES degerlerinin hepsi string."""
        for val in self.alias_dict.values():
            self.assertIsInstance(val, str)

    def test_open_app_empty(self):
        """open_app bos ad ile 'belirtilmedi' doner."""
        result = self.open_app("")
        self.assertIn("belirtilmedi", result)

    def test_open_app_none(self):
        """open_app None ile 'belirtilmedi' doner."""
        result = self.open_app(None)
        self.assertIn("belirtilmedi", result)

    def test_open_app_not_windows(self):
        """open_app Windows degilse platform hatasi doner (os.name != 'nt' iken)."""
        import os
        if os.name != "nt":
            result = self.open_app("chrome")
            self.assertIn("calismiyor", result)


# =============================================================================
# 13. CALENDAR — SAF FONKSIYON TESTLERI
# =============================================================================
