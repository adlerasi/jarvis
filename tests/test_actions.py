from __future__ import annotations

import json
import os
import importlib
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


class TestActionModules(unittest.TestCase):
    """Tum 14 action modulunun import edilebilirlik testi."""

    def test_actions_package_importable(self):
        """actions/ paketi import edilebilmeli."""
        import actions  # noqa: F401

    def test_all_action_modules_importable(self):
        """Her action modulu ayri ayri import edilebilmeli."""
        modules = [
            "actions.open_app",
            "actions.sys_info",
            "actions.weather",
            "actions.reminders",
            "actions.calendar",
            "actions.tts",
            "actions.windows_utils",
            "actions.browser",
            "actions.shell",
            "actions.whatsapp",
            "actions.media",
            "actions.youtube_stats",
            "actions.screen_vision",
            "actions.health",
        ]
        for mod_name in modules:
            with self.subTest(module=mod_name):
                if mod_name == "actions.screen_vision" and not HAS_GOOGLE_GENAI:
                    self.skipTest("google-genai paketi kurulu degil")
                try:
                    importlib.import_module(mod_name)
                except ImportError as e:
                    self.fail(f"{mod_name} import edilemedi: {e}")

    def test_health_module_has_expected_functions(self):
        """health modulunde beklenen fonksiyonlar var."""
        mod = importlib.import_module("actions.health")
        for name in ("get_health_data", "get_welcome_health_summary", "_normalize_query", "_extract_target_date", "_v", "_age_str", "_date_from_file"):
            self.assertTrue(hasattr(mod, name), f"Eksik: {name}")

    def test_tts_module_has_expected_functions(self):
        """tts modulunde beklenen fonksiyonlar var."""
        mod = importlib.import_module("actions.tts")
        for name in ("speak_text", "get_available_voices"):
            self.assertTrue(hasattr(mod, name), f"Eksik: {name}")

    def test_youtube_stats_has_expected_functions(self):
        """youtube_stats modulunde beklenen fonksiyonlar var."""
        mod = importlib.import_module("actions.youtube_stats")
        for name in ("get_youtube_channel_report", "_format_int", "_parse_duration_seconds", "_normalize_channel_ref"):
            self.assertTrue(hasattr(mod, name), f"Eksik: {name}")

    def test_windows_utils_has_expected_functions(self):
        """windows_utils modulunde beklenen fonksiyonlar var."""
        mod = importlib.import_module("actions.windows_utils")
        for name in ("open_url", "copy_to_clipboard", "speak_with_windows", "open_uri", "open_windows_app"):
            self.assertTrue(hasattr(mod, name), f"Eksik: {name}")
