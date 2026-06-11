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


class TestConfig(unittest.TestCase):
    """Konfigurasyon dosyasi testleri."""

    def test_pyrightconfig_valid_json(self):
        """pyrightconfig.json gecerli JSON ve dogru ayarlar."""
        config_file = BASE_DIR / "pyrightconfig.json"
        self.assertTrue(config_file.exists())
        with open(config_file) as f:
            cfg = json.load(f)
        self.assertEqual(cfg.get("typeCheckingMode"), "basic")
        self.assertIn("pythonVersion", cfg)
        self.assertIn("pythonVersion", cfg)

    def test_requirements_has_versions(self):
        """requirements.txt version pin iceriyor."""
        req_file = BASE_DIR / "requirements.txt"
        content = req_file.read_text()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            self.assertIn(">=", line, f"'{line}' version pin'i yok")

    def test_app_config_defaults(self):
        """app_config DEFAULT_CONFIG 7 anahtar icermeli."""
        from app_config import DEFAULT_CONFIG
        self.assertIsInstance(DEFAULT_CONFIG, dict)
        for key in ("gemini_api_key", "voice", "backend_type", "ollama_model", "ollama_tts_voice", "youtube_api_key", "youtube_channel_handle"):
            self.assertIn(key, DEFAULT_CONFIG, f"Eksik default: {key}")

    def test_app_config_load_returns_dict(self):
        """load_app_config() dict doner."""
        from app_config import load_app_config
        cfg = load_app_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn("gemini_api_key", cfg)

    def test_app_config_save_and_reload(self):
        """save_app_config + load_app_config dongusu calisir."""
        from app_config import load_app_config, save_app_config
        original = load_app_config()
        try:
            # Gecici bir deger yaz
            save_app_config({"voice": "TEST_VOICE"})
            reloaded = load_app_config()
            self.assertEqual(reloaded.get("voice"), "TEST_VOICE")
        finally:
            # Orijinal degeri geri yaz
            save_app_config(original)

    def test_get_app_config_value(self):
        """get_app_config_value() dogru deger doner."""
        from app_config import get_app_config_value
        self.assertIsNotNone(get_app_config_value("voice"))

    def test_has_gemini_api_key(self):
        """has_gemini_api_key() bool doner (su an false olabilir)."""
        from app_config import has_gemini_api_key
        result = has_gemini_api_key()
        self.assertIsInstance(result, bool)
        # Gercek API key olabilir veya olmayabilir, sadece tip kontrol


# =============================================================================
# 3. AKSIYON MODUL IMPORT'LARI (TAM KAPSAM)
# =============================================================================
