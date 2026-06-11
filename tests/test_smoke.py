#!/usr/bin/env python3
from __future__ import annotations

"""
JARVIS — Kapsamli Test
Proje yapisi, modul import'lari, konfigurasyon, saf fonksiyon testleri.
Mock sadece URL yan etkilerini engellemek icin kullanilir.
"""

import importlib
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


# =============================================================================
# 1. PROJE YAPISI

# ── Re-exports from split test modules (backward compat) ──
from tests.test_actions import *
from tests.test_browser import *
from tests.test_calendar import *
from tests.test_config import *
from tests.test_health import *
from tests.test_main import *
from tests.test_media import *
from tests.test_memory import *
from tests.test_noise_suppressor import *
from tests.test_open_app import *
from tests.test_reminders import *
from tests.test_screen_vision import *
from tests.test_shell import *
from tests.test_skills import *
from tests.test_sys_info import *
from tests.test_text_utils import *
from tests.test_tool_registry import *
from tests.test_tts import *
from tests.test_ui import *
from tests.test_weather import *
from tests.test_whatsapp import *
from tests.test_windows_utils import *
from tests.test_youtube import *
from tests.test_streaming_stt import *
from tests.test_streaming_tts import *
from tests.test_fahrettin_vad import *
from tests.test_vad_engine import *
from tests.test_audio_buffer import *
from tests.test_barge_in import *
from tests.test_emotion_tts import *
from tests.test_wake_word import *
from tests.test_disk_predictor import *
from tests.test_process_timeline import *
from tests.test_network_anomaly import *
from tests.test_location import *
from tests.test_service_monitor import *
from tests.test_cron_web_ui import *
from tests.test_file_watcher import *
from tests.test_orb_canvas import *
from tests.test_sound_manager import *
from tests.test_draw_utils import *
from tests.test_provider_base import *
from tests.test_local_llm import *
from tests.test_thinking_aloud import *
from tests.test_proactive_voice import *
from tests.test_voice_manager import *
from tests.test_microphone import *
from tests.test_audio_system import *
from tests.test_ui_text_utils import *
from tests.test_conversation_transcript import *
from tests.test_voice_memory import *
from tests.test_app_config import *
from tests.test_skill_manager import *
from tests.test_multimodal import *
from tests.test_file_guardian import *
from tests.test_network_monitor import *
from tests.test_pipeline import *
from tests.test_process_manager import *
from tests.test_system_cron import *
from tests.test_system_doctor import *
from tests.test_tool_dispatch import *
from tests.test_skill_debugging import *
from tests.test_skill_file_manager import *
from tests.test_skill_greeting import *
from tests.test_skill_process_control import *
from tests.test_skill_scheduler import *
from tests.test_skill_services import *
from tests.test_skill_system_health import *
from tests.test_skill_voice_coding import *
from tests.test_hardware_detector import *

# =============================================================================

class TestProjectStructure(unittest.TestCase):
    """Proje dizin yapisi dogrulama testleri."""

    def test_core_is_package(self):
        """core/ __init__.py icermeli."""
        init_file = BASE_DIR / "core" / "__init__.py"
        self.assertTrue(init_file.exists())

    def test_icon_dir_exists(self):
        """Icon/ dizini ve ikonlar mevcut olmali."""
        icon_dir = BASE_DIR / "Icon"
        self.assertTrue(icon_dir.is_dir())
        self.assertTrue((icon_dir / "instagram-logo.png").exists())
        self.assertTrue((icon_dir / "youtube-logo.png").exists())

    def test_no_log_files_in_root(self):
        """Kok dizinde *.log yok."""
        logs = list(BASE_DIR.glob("*.log"))
        self.assertEqual(len(logs), 0, f"Kokte log: {logs}")

    def test_no_postscript_artifacts(self):
        """PostScript artifact dosyalari silinmis."""
        for name in ("logging", "threading", "sys", "traceback"):
            self.assertFalse((BASE_DIR / name).exists(), f"Hala var: {name}")

    def test_gitignore_updated(self):
        """.gitignore gerekli pattern'leri iceriyor."""
        gitignore = BASE_DIR / ".gitignore"
        content = gitignore.read_text()
        for pattern in ("*.log", "logs/", "Icon/", ".env", ".idea/"):
            self.assertIn(pattern, content)

    def test_prompt_file_exists(self):
        """core/prompt.txt mevcut ve 100 karakterden uzun."""
        prompt_file = BASE_DIR / "core" / "prompt.txt"
        self.assertTrue(prompt_file.exists())
        self.assertGreater(len(prompt_file.read_text()), 100)

    def test_helpers_bin_readme_exists(self):
        """helpers/bin/README.md mevcut."""
        self.assertTrue((BASE_DIR / "helpers" / "bin" / "README.md").exists())

    def test_requirements_txt_exists(self):
        """requirements.txt mevcut."""
        self.assertTrue((BASE_DIR / "requirements.txt").exists())

    def test_setup_ps1_exists(self):
        """setup.ps1 mevcut."""
        self.assertTrue((BASE_DIR / "setup.ps1").exists())

    def test_config_example_json_exists(self):
        """config/api_keys.example.json mevcut ve gecerli JSON."""
        example = BASE_DIR / "config" / "api_keys.example.json"
        self.assertTrue(example.exists())
        with open(example) as f:
            cfg = json.load(f)
        self.assertIsInstance(cfg, dict)
        # Tum zorunlu anahtarlar var mi?
        for key in ("gemini_api_key", "voice", "backend_type", "ollama_model", "ollama_tts_voice", "youtube_api_key", "youtube_channel_handle"):
            self.assertIn(key, cfg, f"Eksik anahtar: {key}")

    def test_gitignore_has_api_keys(self):
        """.gitignore api_keys.json iceriyor."""
        gitignore = BASE_DIR / ".gitignore"
        content = gitignore.read_text()
        self.assertIn("api_keys.json", content)


# =============================================================================
# 2. KONFIGURASYON
# =============================================================================
