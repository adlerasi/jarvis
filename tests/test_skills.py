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


class TestSkillModules(unittest.TestCase):
    """15 skill modulunun import edilebilirlik testi."""

    def test_skill_modules_importable(self):
        """Her skill modulu ayri ayri import edilebilmeli."""
        modules = [
            "skills.browser.browser_skill",
            "skills.system_health.system_health_skill",
            "skills.process_control.process_control_skill",
            "skills.file_manager.file_manager_skill",
            "skills.weather.weather_skill",
            "skills.youtube.youtube_skill",
            "skills.vision.vision_skill",
            "skills.calendar.calendar_skill",
            "skills.reminders.reminders_skill",
            "skills.whatsapp.whatsapp_skill",
            "skills.media.media_skill",
            "skills.network.network_skill",
            "skills.scheduler.scheduler_skill",
            "skills.services.services_skill",
            "skills.greeting.greeting_skill",
        ]
        for mod_name in modules:
            with self.subTest(module=mod_name):
                try:
                    importlib.import_module(mod_name)
                except ImportError as e:
                    self.fail(f"{mod_name} import edilemedi: {e}")

    def test_core_skill_manager_importable(self):
        """core.skill_manager import edilebilmeli."""
        importlib.import_module("core.skill_manager")

    def test_skill_manager_loads_all_skills(self):
        """SkillManager tum skill'leri yukleyebilmeli."""
        from core.skill_manager import get_skill_manager
        sm = get_skill_manager()
        self.assertGreaterEqual(sm.get_skill_count(), 17)
        expected_skills = [
            "browser",
            "system-health-v1", "process-control-v1", "file-manager-v1",
            "weather-v1", "youtube-v1", "vision-v1",
            "calendar-v1", "reminders-v1", "whatsapp-v1", "media-v1",
            "network-v1", "scheduler-v1", "services-v1",
            "greeting-v1", "voice-coding-v1",
        ]
        for s in expected_skills:
            self.assertIn(s, sm.list_skills(), f"Eksik skill: {s}")

    def test_each_skill_has_route_function(self):
        """Her skill'in route_xxx_request fonksiyonu var."""
        skills = [
            ("skills.browser.browser_skill", "route_browser_request"),
            ("skills.system_health.system_health_skill", "route_system_health_request"),
            ("skills.process_control.process_control_skill", "route_process_request"),
            ("skills.file_manager.file_manager_skill", "route_file_request"),
            ("skills.weather.weather_skill", "route_weather_request"),
            ("skills.youtube.youtube_skill", "route_youtube_request"),
            ("skills.vision.vision_skill", "route_vision_request"),
            ("skills.calendar.calendar_skill", "route_calendar_request"),
            ("skills.reminders.reminders_skill", "route_reminders_request"),
            ("skills.whatsapp.whatsapp_skill", "route_whatsapp_request"),
            ("skills.media.media_skill", "route_media_request"),
            ("skills.network.network_skill", "route_network_request"),
            ("skills.scheduler.scheduler_skill", "route_scheduler_request"),
            ("skills.services.services_skill", "route_services_request"),
            ("skills.greeting.greeting_skill", "route_greeting_request"),
        ]
        for mod_name, func_name in skills:
            with self.subTest(module=mod_name):
                mod = importlib.import_module(mod_name)
                self.assertTrue(hasattr(mod, func_name), f"Eksik: {func_name}")


# =============================================================================
# 4. YOUTUBE_STATS — SAF FONKSIYON TESTLERI
# =============================================================================
