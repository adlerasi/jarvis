from __future__ import annotations

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestSchedulerSkill(unittest.TestCase):
    """scheduler_skill pure function tests."""

    def setUp(self):
        self.patchers = [
            patch("skills.scheduler.scheduler_skill.list_cron_jobs",
                  return_value="1. health_check (günlük 08:00) [aktif]"),
            patch("skills.scheduler.scheduler_skill.add_cron_job",
                  return_value="Görev eklendi (ID: 5)."),
            patch("skills.scheduler.scheduler_skill.remove_cron_job",
                  return_value="Görev silindi."),
        ]
        for p in self.patchers:
            p.start()
        from skills.scheduler.scheduler_skill import (
            classify_scheduler_intent,
            execute_scheduler_skill,
            route_scheduler_request,
            _parse_schedule,
            _extract_job_name,
            _extract_command,
        )
        self.classify = classify_scheduler_intent
        self.execute = execute_scheduler_skill
        self.route = route_scheduler_request
        self.parse_schedule = _parse_schedule
        self.extract_job_name = _extract_job_name
        self.extract_command = _extract_command

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_classify_list_jobs(self):
        intent, params = self.classify("görevleri listele")
        self.assertEqual(intent, "list_jobs")

    def test_classify_add_job(self):
        intent, params = self.classify("her gün saat 08:00'de sistem kontrol görevi ekle")
        self.assertEqual(intent, "add_job")
        self.assertIn("name", params)
        self.assertIn("command", params)
        self.assertIn("schedule_type", params)

    def test_classify_remove_job(self):
        intent, params = self.classify("1 numaralı görevi sil")
        self.assertEqual(intent, "remove_job")
        self.assertEqual(params["job_id"], 1)

    def test_classify_none(self):
        intent, params = self.classify("bana bir kahve getir")
        self.assertEqual(intent, "none")

    def test_route_scheduler_request_match(self):
        result = self.route("görevleri listele")
        self.assertIsNotNone(result)

    def test_route_scheduler_request_no_match(self):
        result = self.route("havadan sudan konuşma")
        self.assertIsNone(result)

    def test_execute_list_jobs(self):
        result = self.execute("list_jobs", {"enabled_only": False})
        self.assertIn("health_check", result)

    def test_execute_add_job(self):
        result = self.execute("add_job", {"name": "Test", "command": "health_check",
                                          "schedule_type": "daily", "schedule_value": "08:00"})
        self.assertIn("eklendi", result)

    def test_execute_remove_job(self):
        result = self.execute("remove_job", {"job_id": 1})
        self.assertIn("silindi", result)

    def test_execute_unknown(self):
        result = self.execute("unknown_action", {})
        self.assertIn("Bilinmeyen", result)

    def test_parse_schedule_interval(self):
        sched_type, value = self.parse_schedule("30 dakikada bir çalıştır")
        self.assertEqual(sched_type, "interval")
        self.assertEqual(value, "1800")

    def test_parse_schedule_daily(self):
        sched_type, value = self.parse_schedule("her gün saat 09:30")
        self.assertEqual(sched_type, "daily")
        self.assertEqual(value, "09:30")

    def test_parse_schedule_daily_fallback(self):
        sched_type, value = self.parse_schedule("günlük kontrol")
        self.assertEqual(sched_type, "daily")

    def test_parse_schedule_weekly(self):
        sched_type, value = self.parse_schedule("her hafta bir kere")
        self.assertEqual(sched_type, "weekly")

    def test_extract_job_name_default(self):
        name = self.extract_job_name("görev ekle")
        self.assertEqual(name, "Yeni Gorev")

    def test_extract_job_name_custom(self):
        name = self.extract_job_name("sistem kontrol görevi ekle")
        self.assertEqual(name, "Sistem kontrol")

    def test_extract_command_temp(self):
        cmd = self.extract_command("temp dosyaları temizle")
        self.assertEqual(cmd, "temp_cleanup")

    def test_extract_command_health(self):
        cmd = self.extract_command("sistem sağlık kontrolü yap")
        self.assertEqual(cmd, "health_check")

    def test_extract_command_recycle(self):
        cmd = self.extract_command("çöp kutusunu temizle")
        self.assertEqual(cmd, "recycle_cleanup")
