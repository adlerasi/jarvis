from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestDebuggingSkill(unittest.TestCase):
    """debugging_jarvis_skill pure function tests."""

    def setUp(self):
        from skills.debugging_jarvis.debugging_jarvis_skill import (
            classify_debug_intent,
            route_debugging_jarvis_request,
            CAT_AUDIO, CAT_UI, CAT_SKILL, CAT_SYSTEM, CAT_NETWORK,
            CAT_GENERAL, CAT_LOG,
        )
        self.classify = classify_debug_intent
        self.route = route_debugging_jarvis_request
        self.CAT_AUDIO = CAT_AUDIO
        self.CAT_UI = CAT_UI
        self.CAT_SKILL = CAT_SKILL
        self.CAT_SYSTEM = CAT_SYSTEM
        self.CAT_NETWORK = CAT_NETWORK
        self.CAT_GENERAL = CAT_GENERAL
        self.CAT_LOG = CAT_LOG

    def test_classify_audio_no_sound(self):
        cat = self.classify("sesim gelmiyor")
        self.assertEqual(cat, self.CAT_AUDIO)

    def test_classify_audio_microphone(self):
        cat = self.classify("mikrofon çalışmıyor")
        self.assertEqual(cat, self.CAT_AUDIO)

    def test_classify_audio_rnnoise(self):
        cat = self.classify("rnnoise yüklenemedi")
        self.assertEqual(cat, self.CAT_AUDIO)

    def test_classify_audio_noise(self):
        cat = self.classify("gürültü var seste")
        self.assertEqual(cat, self.CAT_AUDIO)

    def test_classify_ui_frozen(self):
        cat = self.classify("UI dondu")
        self.assertEqual(cat, self.CAT_UI)

    def test_classify_ui_window(self):
        cat = self.classify("pencere açılmıyor")
        self.assertEqual(cat, self.CAT_UI)

    def test_classify_ui_animation(self):
        cat = self.classify("orb animasyonu takıldı")
        self.assertEqual(cat, self.CAT_UI)

    def test_classify_skill_not_loading(self):
        cat = self.classify("skill yüklenmedi")
        self.assertEqual(cat, self.CAT_SKILL)

    def test_classify_skill_import(self):
        cat = self.classify("import hatası skill")
        self.assertEqual(cat, self.CAT_SKILL)

    def test_classify_skill_unknown_tool(self):
        # "bilinmeyen araç hatası" → skill pattern fails 2nd segment,
        # falls through to general keyword "hata" → CAT_GENERAL
        cat = self.classify("bilinmeyen araç hatası")
        self.assertEqual(cat, self.CAT_GENERAL)

    def test_classify_system_platform(self):
        cat = self.classify("windows uyumsuzluk hatası")
        self.assertEqual(cat, self.CAT_SYSTEM)

    def test_classify_system_permission(self):
        cat = self.classify("yetki hatası alıyorum")
        self.assertEqual(cat, self.CAT_SYSTEM)

    def test_classify_network_internet(self):
        cat = self.classify("internet yok bağlantı kuramadım")
        self.assertEqual(cat, self.CAT_NETWORK)

    def test_classify_network_ollama(self):
        cat = self.classify("ollama bağlanamıyor")
        self.assertEqual(cat, self.CAT_NETWORK)

    def test_classify_network_gemini(self):
        cat = self.classify("gemini api hatası")
        self.assertEqual(cat, self.CAT_NETWORK)

    def test_classify_log(self):
        cat = self.classify("logları göster")
        self.assertEqual(cat, self.CAT_LOG)

    def test_classify_general_error(self):
        cat = self.classify("hata var debug yap")
        self.assertEqual(cat, self.CAT_GENERAL)

    def test_classify_general_calismiyor(self):
        cat = self.classify("bu program çalışmıyor")
        self.assertEqual(cat, self.CAT_GENERAL)

    def test_classify_none(self):
        cat = self.classify("güzel bir gün")
        self.assertEqual(cat, "none")

    def test_classify_empty_string(self):
        cat = self.classify("")
        self.assertEqual(cat, "none")

    def test_route_empty_string(self):
        result = self.route("")
        self.assertIsNone(result)

    def test_route_none_text(self):
        result = self.route("   ")
        self.assertIsNone(result)

    def test_route_debug_request(self):
        result = self.route("sesim gelmiyor")
        self.assertIsNotNone(result)
        self.assertIn("Debug", result)

    def test_route_no_match(self):
        # "güzel bir gün" has no debug keywords → None
        result = self.route("güzel bir gün")
        self.assertIsNone(result)

    def test_route_ui_debug(self):
        result = self.route("UI dondu ne yapmalıyım")
        self.assertIsNotNone(result)

    def test_route_network_debug_none(self):
        # "internete bağlanamıyorum" — network patterns need
        # yok/kurulamadi/kesik/kopuk/koptu/zayıf after internet keyword
        result = self.route("internete bağlanamıyorum")
        self.assertIsNone(result)

    @patch("skills.debugging_jarvis.debugging_jarvis_skill._run_cmd",
           return_value="1 received")
    def test_execute_debug_audio(self, mock_run):
        result = self.route("sesim gelmiyor")
        self.assertIsNotNone(result)
        self.assertIn("Debug", result)
