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


class TestMedia(unittest.TestCase):
    """media modulu — validation testleri."""

    def setUp(self):
        from actions import media
        self.mod = media

    def test_play_media_empty_query(self):
        """play_media bos sorguyla hata doner."""
        result = self.mod.play_media("")
        self.assertIn("belirtilmedi", result)

    def test_play_media_none_query(self):
        """play_media None sorguyla hata doner."""
        result = self.mod.play_media(None)
        self.assertIn("belirtilmedi", result)

    def test_play_media_youtube_provider(self):
        """play_media youtube provider'ini algilar (hata yolu)."""
        with patch("actions.media.browser_control") as mock_bc:
            mock_bc.return_value = "YouTube test"
            result = self.mod.play_media("test sarki", provider="youtube")
            self.assertIsInstance(result, str)
            mock_bc.assert_called_once_with("play_youtube", query="test sarki")


# =============================================================================
# 19. SCREEN VISION — SAF FONKSIYON TESTLERI
# =============================================================================
