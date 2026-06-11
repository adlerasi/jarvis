from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestFileManagerSkill(unittest.TestCase):
    """file_manager_skill pure function tests."""

    def setUp(self):
        self.patchers = [
            patch("skills.file_manager.file_manager_skill.find_large_files",
                  return_value="Büyük dosyalar: /tmp/big.bin (500 MB)"),
            patch("skills.file_manager.file_manager_skill.find_duplicate_files",
                  return_value="Mükerrer dosya bulunamadı."),
            patch("skills.file_manager.file_manager_skill.cleanup_folder",
                  return_value="Temizlik yapıldı."),
            patch("skills.file_manager.file_manager_skill.get_folder_summary",
                  return_value="/tmp: 10 dosya, 2.1 GB"),
        ]
        for p in self.patchers:
            p.start()
        from skills.file_manager.file_manager_skill import (
            classify_file_intent,
            execute_file_skill,
            route_file_request,
        )
        self.classify = classify_file_intent
        self.execute = execute_file_skill
        self.route = route_file_request

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_classify_find_large(self):
        intent, params = self.classify("büyük dosyaları bul")
        self.assertEqual(intent, "find_large")

    def test_classify_duplicate(self):
        intent, params = self.classify("yinelenen dosyaları tara")
        self.assertEqual(intent, "find_duplicate")

    def test_classify_cleanup(self):
        intent, params = self.classify("downloads klasörünü temizle")
        self.assertEqual(intent, "cleanup_folder")

    def test_classify_folder_summary(self):
        intent, params = self.classify("downloads özeti")
        self.assertEqual(intent, "folder_summary")

    def test_classify_none(self):
        intent, params = self.classify("bugün hava nasıl")
        self.assertEqual(intent, "none")

    def test_classify_with_size(self):
        intent, params = self.classify("500 mb üzeri dosyaları bul")
        self.assertEqual(intent, "find_large")

    def test_route_file_request_match(self):
        result = self.route("büyük dosyaları göster")
        self.assertIsNotNone(result)
        self.assertIn("Büyük dosya", result)

    def test_route_file_request_no_match(self):
        result = self.route("bugün hava nasıl")
        self.assertIsNone(result)

    def test_execute_find_large(self):
        result = self.execute("find_large", {"path": "/tmp", "min_size_mb": 100})
        self.assertIn("Büyük dosya", result)

    def test_execute_unknown_action(self):
        result = self.execute("unknown_action", {})
        self.assertIn("Bilinmeyen", result)
