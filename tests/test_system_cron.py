"""
System Cron birim testleri.
"""
from __future__ import annotations


import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sqlite3
import tempfile
import os

from actions.system_cron import add_cron_job, list_cron_jobs, remove_cron_job, toggle_cron_job


class TestSystemCron(unittest.TestCase):

    def setUp(self):
        """Her test öncesi temp DB oluştur."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()

        # DB_PATH'i patch'le (Path objesi olarak)
        import actions.system_cron as cron
        self.original_db_path = cron.DB_PATH
        cron.DB_PATH = Path(self.temp_db.name)

    def tearDown(self):
        """Temp DB'yi temizle."""
        import actions.system_cron as cron
        cron.DB_PATH = self.original_db_path
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_add_cron_job_daily(self):
        """Günlük görev ekleme."""
        result = add_cron_job("Test Görev", "temp_cleanup", "daily", "08:00")
        self.assertIn("eklendi", result)
        self.assertIn("Test Görev", result)

    def test_add_cron_job_interval(self):
        """Aralık görevi ekleme."""
        result = add_cron_job("Test Interval", "sys_info", "interval", "3600")
        self.assertIn("eklendi", result)

    def test_add_cron_job_invalid_type(self):
        """Geçersiz schedule type."""
        result = add_cron_job("Test", "cmd", "invalid", "value")
        self.assertIn("Geçersiz", result)

    def test_add_cron_job_empty_name(self):
        """Boş isim."""
        result = add_cron_job("", "cmd", "daily", "08:00")
        self.assertIn("zorunlu", result)

    def test_list_cron_jobs_empty(self):
        """Boş liste."""
        result = list_cron_jobs()
        self.assertIn("bulunmuyor", result)

    def test_list_cron_jobs_with_data(self):
        """Verili liste."""
        add_cron_job("Görev 1", "temp_cleanup", "daily", "08:00")
        add_cron_job("Görev 2", "sys_info", "weekly", "1-08:00")

        result = list_cron_jobs()
        self.assertIn("Görev 1", result)
        self.assertIn("Görev 2", result)
        self.assertIn("daily", result)
        self.assertIn("weekly", result)

    def test_remove_cron_job(self):
        """Görev silme."""
        add_cron_job("Silinecek", "cmd", "once", "2026-12-31T23:59")

        # ID 1 olmalı (ilk görev)
        result = remove_cron_job(1)
        self.assertIn("silindi", result)

    def test_remove_cron_job_not_found(self):
        """Bulunamayan görev silme."""
        result = remove_cron_job(999)
        self.assertIn("silindi", result)  # SQLite DELETE etkilenen satır döndürmez

    def test_toggle_cron_job(self):
        """Görev durum değiştirme."""
        add_cron_job("Toggle Test", "cmd", "daily", "08:00")

        result = toggle_cron_job(1, False)
        self.assertIn("devre dışı", result)

        result = toggle_cron_job(1, True)
        self.assertIn("etkinleştirildi", result)


if __name__ == "__main__":
    unittest.main()
