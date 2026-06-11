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


class TestWindowsUtils(unittest.TestCase):
    """windows_utils pure fonksiyon testleri."""

    def test_open_url_does_not_crash(self):
        """open_url cagrildiginda exception firlatmaz."""
        from actions.windows_utils import open_url
        with patch("actions.windows_utils.webbrowser.open") as mock_open:
            try:
                open_url("https://example.com")
            except Exception as e:
                self.fail(f"open_url exception firlatti: {e}")
            mock_open.assert_called_once_with("https://example.com", new=2)


# =============================================================================
# 11. WEATHER — SAF FONKSIYON TESTLERI
# =============================================================================
