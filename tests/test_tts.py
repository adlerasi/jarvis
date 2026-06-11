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


class TestTTS(unittest.TestCase):
    """tts modulu pure fonksiyon testleri — ses cikisi yok."""

    def setUp(self):
        from actions import tts
        self.mod = tts

    def test_edge_voice_name(self):
        """_edge_voice_name dogru ses adini doner."""
        self.assertEqual(self.mod._edge_voice_name("edge-ahmet"), "tr-TR-AhmetNeural")
        self.assertEqual(self.mod._edge_voice_name("edge-emel"), "tr-TR-EmelNeural")
        self.assertEqual(self.mod._edge_voice_name("bilinmeyen"), "tr-TR-AhmetNeural")


# =============================================================================
# 10. WINDOWS_UTILS — SAF FONKSIYON TESTLERI
# =============================================================================
