from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestServicesSkill(unittest.TestCase):
    """services_skill pure function tests."""

    def setUp(self):
        self.patchers = [
            patch("skills.services.services_skill.list_services",
                  return_value="nginx: running\nmysql: stopped"),
            patch("skills.services.services_skill.control_service",
                  return_value="nginx başlatıldı."),
        ]
        for p in self.patchers:
            p.start()
        from skills.services.services_skill import (
            classify_services_intent,
            execute_services_skill,
            route_services_request,
            _extract_service_name,
        )
        self.classify = classify_services_intent
        self.execute = execute_services_skill
        self.route = route_services_request
        self.extract_name = _extract_service_name

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_extract_service_name_mysql(self):
        name, action = self.extract_name("mysql servisini başlat")
        self.assertEqual(name, "mysql")

    def test_extract_service_name_nginx(self):
        name, action = self.extract_name("nginx durumu")
        self.assertEqual(name, "nginx")

    def test_extract_service_action_start(self):
        name, action = self.extract_name("postgresql servisini başlat")
        self.assertEqual(action, "start")

    def test_extract_service_action_stop(self):
        name, action = self.extract_name("redis servisini durdur")
        self.assertEqual(action, "stop")

    def test_extract_service_action_restart(self):
        name, action = self.extract_name("apache servisini yeniden başlat")
        self.assertEqual(action, "restart")

    def test_classify_list_services(self):
        intent, params = self.classify("servisleri listele")
        self.assertEqual(intent, "list_services")

    def test_classify_list_services_running(self):
        intent, params = self.classify("çalışan servisleri göster")
        self.assertEqual(intent, "list_services")
        self.assertEqual(params["status_filter"], "running")

    def test_classify_control_service(self):
        intent, params = self.classify("mysql servisini başlat")
        self.assertEqual(intent, "control_service")
        self.assertEqual(params["service_name"], "mysql")
        self.assertEqual(params["action"], "start")

    def test_classify_none(self):
        intent, params = self.classify("merhaba bugün hava nasıl")
        self.assertEqual(intent, "none")

    def test_route_services_request_match(self):
        result = self.route("servisleri listele")
        self.assertIsNotNone(result)

    def test_route_services_request_no_match(self):
        result = self.route("bugün çok güzel bir gün")
        self.assertIsNone(result)

    def test_execute_list_services(self):
        result = self.execute("list_services", {"status_filter": "all", "limit": 20})
        self.assertIn("running", result)

    def test_execute_control_service(self):
        result = self.execute("control_service", {"service_name": "nginx", "action": "start"})
        self.assertIn("başlatıldı", result)

    def test_execute_unknown(self):
        result = self.execute("unknown_action", {})
        self.assertIn("Bilinmeyen", result)

    def test_classify_keyword_fallback(self):
        intent, params = self.classify("mysql çalışıyor mu")
        self.assertEqual(intent, "control_service")
