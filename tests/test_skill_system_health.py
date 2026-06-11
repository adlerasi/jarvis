from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestSystemHealthSkill(unittest.TestCase):
    """system_health_skill pure function tests."""

    def setUp(self):
        # Import module first so patch attribute resolution finds it
        from skills.system_health.system_health_skill import (
            classify_system_health_intent,
            execute_system_health_skill,
            route_system_health_request,
        )
        self.classify = classify_system_health_intent
        self.execute = execute_system_health_skill
        self.route = route_system_health_request

        self.patchers = [
            patch("skills.system_health.system_health_skill.get_system_health",
                  return_value="CPU: %12, RAM: %45, Disk: %60"),
            patch("skills.system_health.system_health_skill.cleanup_temp_files",
                  return_value="Geçici dosyalar temizlendi (500 MB)."),
            patch("skills.system_health.system_health_skill.cleanup_recycle_bin",
                  return_value="Çöp kutusu boşaltıldı."),
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_classify_health_check_cpu(self):
        intent, _ = self.classify("cpu kullanımı nedir")
        self.assertEqual(intent, "health_check")

    def test_classify_health_check_system(self):
        intent, _ = self.classify("sistem durumu nasıl")
        self.assertEqual(intent, "health_check")

    def test_classify_health_check_performance(self):
        intent, _ = self.classify("bilgisayar neden yavaş")
        self.assertEqual(intent, "health_check")

    def test_classify_cleanup_temp(self):
        intent, _ = self.classify("geçici dosyaları temizle")
        self.assertEqual(intent, "cleanup_temp")

    def test_classify_cleanup_recycle(self):
        intent, _ = self.classify("çöp kutusunu boşalt")
        self.assertEqual(intent, "cleanup_recycle")

    def test_classify_hava_durumu_should_not_match(self):
        intent, _ = self.classify("hava durumu nasıl")
        self.assertEqual(intent, "none")

    def test_classify_none(self):
        intent, _ = self.classify("merhaba nasılsın")
        self.assertEqual(intent, "none")

    def test_route_system_health_request_match(self):
        result = self.route("sistem durumu")
        self.assertIsNotNone(result)
        self.assertIn("CPU", result)

    def test_route_system_health_request_no_match(self):
        result = self.route("güzel bir gün")
        self.assertIsNone(result)

    def test_route_cleanup_temp(self):
        result = self.route("geçici dosyaları temizle")
        self.assertIsNotNone(result)

    def test_route_cleanup_recycle(self):
        result = self.route("çöp kutusunu boşalt")
        self.assertIsNotNone(result)

    def test_execute_health_check(self):
        result = self.execute("health_check", "all")
        self.assertIn("CPU", result)

    def test_execute_cleanup_temp(self):
        result = self.execute("cleanup_temp")
        self.assertIn("temizlendi", result)

    def test_execute_unknown(self):
        result = self.execute("unknown_action")
        self.assertIn("Bilinmeyen", result)

    def test_classify_fallback_keyword(self):
        intent, _ = self.classify("ram doldu")
        self.assertEqual(intent, "health_check")
