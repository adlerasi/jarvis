from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestProcessControlSkill(unittest.TestCase):
    """process_control_skill pure function tests."""

    def setUp(self):
        self.patchers = [
            patch("skills.process_control.process_control_skill.list_processes",
                  return_value="PID 1234 chrome.exe CPU: %5"),
            patch("skills.process_control.process_control_skill.kill_process",
                  return_value="chrome.exe sonlandırıldı."),
            patch("skills.process_control.process_control_skill.set_process_priority",
                  return_value="Öncelik ayarlandı."),
            patch("skills.process_control.process_control_skill.find_process_by_port",
                  return_value="3000 portu: node.exe (PID 5678)"),
        ]
        for p in self.patchers:
            p.start()
        from skills.process_control.process_control_skill import (
            classify_process_intent,
            execute_process_skill,
            route_process_request,
        )
        self.classify = classify_process_intent
        self.execute = execute_process_skill
        self.route = route_process_request

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_classify_list_processes(self):
        intent, params = self.classify("hangi programlar çalışıyor")
        self.assertEqual(intent, "list_processes")

    def test_classify_kill_process(self):
        intent, params = self.classify("chrome'u kapat")
        self.assertEqual(intent, "kill_process")
        self.assertEqual(params["identifier"], "chrome")

    def test_classify_find_by_port(self):
        intent, params = self.classify("3000 portunu kim kullanıyor")
        self.assertEqual(intent, "find_by_port")
        self.assertEqual(params["port"], 3000)

    def test_classify_set_priority(self):
        intent, params = self.classify("oyuna yüksek öncelik ver")
        self.assertEqual(intent, "set_priority")

    def test_classify_none(self):
        intent, params = self.classify("merhaba nasılsın")
        self.assertEqual(intent, "none")

    def test_route_process_request_match(self):
        result = self.route("çalışan programları listele")
        self.assertIsNotNone(result)

    def test_route_process_request_no_match(self):
        result = self.route("havadan sudan konuşalım")
        self.assertIsNone(result)

    def test_execute_list_processes(self):
        result = self.execute("list_processes", {"sort_by": "cpu", "limit": 10})
        self.assertIn("chrome", result)

    def test_execute_kill_process(self):
        result = self.execute("kill_process", {"identifier": "chrome", "force": False})
        self.assertIn("sonlandırıldı", result)

    def test_execute_unknown(self):
        result = self.execute("unknown_action", {})
        self.assertIn("Bilinmeyen", result)

    def test_classify_ram_sort(self):
        intent, params = self.classify("en çok ram kullanan programlar")
        self.assertEqual(intent, "list_processes")
        self.assertEqual(params["sort_by"], "memory")
