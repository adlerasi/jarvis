from __future__ import annotations

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

BASE_DIR = Path(__file__).resolve().parent.parent


class TestProcessTimeline(unittest.TestCase):
    """ProcessTimeline SQLite tabanli surec izleme testleri."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test_process.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_module_import(self):
        """actions.process_timeline import edilebilmeli."""
        from actions.process_timeline import ProcessTimeline
        self.assertIsNotNone(ProcessTimeline)

    def test_init_creates_db(self):
        """__init__ SQLite DB dosyasini olusturmali."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertTrue(self.db_path.exists())

    def test_init_db_tables(self):
        """DB'de process_events tablosu olusmali."""
        from actions.process_timeline import ProcessTimeline
        import sqlite3
        pt = ProcessTimeline(db_path=self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        self.assertIn(("process_events",), tables)

    def test_categorize_browser(self):
        """_categorize browser kategorisini dogru bulmali."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertEqual(pt._categorize("chrome.exe"), "browser")
        self.assertEqual(pt._categorize("firefox.exe"), "browser")
        self.assertEqual(pt._categorize("msedge.exe"), "browser")

    def test_categorize_game(self):
        """_categorize game kategorisini dogru bulmali."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertEqual(pt._categorize("steam.exe"), "game")
        self.assertEqual(pt._categorize("valorant.exe"), "game")

    def test_categorize_ide(self):
        """_categorize IDE kategorisini dogru bulmali."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertEqual(pt._categorize("Code.exe"), "ide")
        self.assertEqual(pt._categorize("pycharm64.exe"), "ide")
        self.assertEqual(pt._categorize("vim"), "ide")

    def test_categorize_media(self):
        """_categorize media kategorisini dogru bulmali."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertEqual(pt._categorize("spotify.exe"), "media")
        self.assertEqual(pt._categorize("vlc.exe"), "media")

    def test_categorize_communication(self):
        """_categorize iletisim kategorisini dogru bulmali."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertEqual(pt._categorize("discord.exe"), "communication")
        self.assertEqual(pt._categorize("Teams.exe"), "communication")

    def test_categorize_other(self):
        """_categorize bilinmeyeni 'other' olarak dondurmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        self.assertEqual(pt._categorize("unknown_random_process.exe"), "other")

    def test_get_daily_summary_empty(self):
        """get_daily_summary kayit yokken mesaj dondurmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        result = pt.get_daily_summary("2099-01-01")
        self.assertIn("bulunamadı", result)

    def test_get_daily_summary_with_data(self):
        """get_daily_summary veri varken calismali."""
        from actions.process_timeline import ProcessTimeline
        import sqlite3
        pt = ProcessTimeline(db_path=self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO process_events (pid, name, category, start_time, end_time, duration, cpu_avg, ram_peak, date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (1234, "chrome.exe", "browser", time.time() - 3600, time.time(), 3600.0, 5.0, 10.0, "2099-01-01")
        )
        conn.commit()
        conn.close()

        result = pt.get_daily_summary("2099-01-01")
        self.assertNotIn("bulunamadı", result)
        self.assertIn("chrome", result)

    def test_get_current_sessions_empty(self):
        """get_current_sessions poll calismadiysa mesaj dondurmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        result = pt.get_current_sessions()
        self.assertIn("Aktif süreç", result)

    def test_weekly_summary_empty(self):
        """get_weekly_summary kayit yokken mesaj dondurmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        result = pt.get_weekly_summary()
        self.assertIn("bulunamadı", result)

    def test_get_process_stats_empty(self):
        """get_process_stats kayit yokken mesaj dondurmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        result = pt.get_process_stats("nonexistent")
        self.assertIn("bulunamadı", result)

    def test_get_category_breakdown_empty(self):
        """get_category_breakdown kayit yokken mesaj dondurmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        result = pt.get_category_breakdown(days=7)
        self.assertIn("bulunamadı", result)

    def test_get_category_breakdown_with_data(self):
        """get_category_breakdown veri varken calismali."""
        from actions.process_timeline import ProcessTimeline
        import sqlite3
        pt = ProcessTimeline(db_path=self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO process_events (pid, name, category, start_time, end_time, duration, cpu_avg, ram_peak, date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (1234, "chrome.exe", "browser", time.time() - 300, time.time(), 300.0, 5.0, 10.0, "2099-01-01")
        )
        conn.execute(
            """INSERT INTO process_events (pid, name, category, start_time, end_time, duration, cpu_avg, ram_peak, date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (5678, "spotify.exe", "media", time.time() - 600, time.time(), 600.0, 3.0, 8.0, "2099-01-01")
        )
        conn.commit()
        conn.close()

        result = pt.get_category_breakdown(days=365)
        self.assertIn("browser", result)
        self.assertIn("media", result)

    def test_cleanup_old_records(self):
        """cleanup_old_records calisabilmeli."""
        from actions.process_timeline import ProcessTimeline
        pt = ProcessTimeline(db_path=self.db_path)
        result = pt.cleanup_old_records(keep_days=1)
        self.assertIn("temizlendi", result)

    def test_get_process_stats_with_data(self):
        """get_process_stats veri varken calismali."""
        from actions.process_timeline import ProcessTimeline
        import sqlite3
        pt = ProcessTimeline(db_path=self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            """INSERT INTO process_events (pid, name, category, start_time, end_time, duration, cpu_avg, ram_peak, date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (1234, "chrome.exe", "browser", time.time() - 3600, time.time(), 3600.0, 5.0, 10.0, "2099-01-01")
        )
        conn.commit()
        conn.close()

        result = pt.get_process_stats("chrome")
        self.assertNotIn("bulunamadı", result)


class TestProcessTimelineQuickFunctions(unittest.TestCase):
    """poll_processes ve get_today_summary wrapper testleri."""

    def test_poll_processes(self):
        """poll_processes calisabilmeli."""
        from actions.process_timeline import poll_processes
        result = poll_processes()
        self.assertIsInstance(result, str)

    def test_get_today_summary(self):
        """get_today_summary calisabilmeli."""
        from actions.process_timeline import get_today_summary
        result = get_today_summary()
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
