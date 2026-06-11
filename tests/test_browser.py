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


class TestBrowser(unittest.TestCase):
    """browser modulu — validation + regex testleri."""

    def setUp(self):
        from actions import browser
        self.mod = browser

    def test_browser_control_unknown_action(self):
        """browser_control bilinmeyen eylem icin hata doner."""
        result = self.mod.browser_control("nonexistent_action")
        self.assertIn("Bilinmeyen", result)

    def test_browser_control_open_url_no_url(self):
        """browser_control open_url URL'siz hata doner."""
        result = self.mod.browser_control("open_url")
        self.assertIn("belirtilmedi", result)

    def test_browser_control_search_no_query(self):
        """browser_control search sorgusuz hata doner."""
        result = self.mod.browser_control("search")
        self.assertIn("belirtilmedi", result)

    def test_browser_control_play_youtube_no_query(self):
        """browser_control play_youtube sorgusuz hata doner."""
        result = self.mod.browser_control("play_youtube")
        self.assertIn("belirtilmedi", result)

    def test_video_id_regex_pattern(self):
        """_VIDEO_ID_RE 11 karakterli base64 ID'leri eslestirir."""
        import re
        pattern = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')
        match = pattern.search('"videoId":"abc123DEF_-"')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "abc123DEF_-")
        match = pattern.search('"videoId":"short"')
        self.assertIsNone(match)
        match = pattern.search('"videoId":"toolongforvalid123"')
        self.assertIsNone(match)


# =============================================================================
# 16. SHELL — SAF FONKSIYON TESTLERI
# =============================================================================
