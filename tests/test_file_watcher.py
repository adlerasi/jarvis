from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

BASE_DIR = Path(__file__).resolve().parent.parent


class TestFileWatcher(unittest.TestCase):
    """actions/watchdog/file_watcher pure fonksiyon testleri."""

    def test_module_import(self):
        """watchdog.file_watcher import edilebilmeli."""
        from actions.watchdog import file_watcher
        self.assertIsNotNone(file_watcher)

    def test_file_watcher_class(self):
        """FileWatcher sinifi mevcut olmali."""
        from actions.watchdog.file_watcher import FileWatcher
        self.assertIsNotNone(FileWatcher)

    def test_event_handler_class(self):
        """JARVISEventHandler sinifi mevcut olmali."""
        from actions.watchdog.file_watcher import JARVISEventHandler
        self.assertIsNotNone(JARVISEventHandler)

    def test_critical_extensions(self):
        """CRITICAL_EXTENSIONS Windows yurutulebilir uzantilarini icermeli."""
        from actions.watchdog.file_watcher import FileWatcher
        exts = FileWatcher.CRITICAL_EXTENSIONS
        self.assertIsInstance(exts, set)
        self.assertIn(".exe", exts)
        self.assertIn(".zip", exts)
        self.assertIn(".ps1", exts)
        self.assertIn(".bat", exts)

    def test_max_history(self):
        """MAX_HISTORY 100 olmali."""
        from actions.watchdog.file_watcher import FileWatcher
        self.assertEqual(FileWatcher.MAX_HISTORY, 100)

    def test_format_event_created(self):
        """_format_event olusturma olayini dogru bicimlendirmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        result = fw._format_event("created", "/tmp/test.py", None)
        self.assertIn("test.py", result)
        self.assertIn("created", result)

    def test_format_event_modified(self):
        """_format_event degisiklik olayini dogru bicimlendirmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        result = fw._format_event("modified", "/tmp/test.py", None)
        self.assertIn("test.py", result)
        self.assertIn("modified", result)

    def test_format_event_deleted(self):
        """_format_event silme olayini dogru bicimlendirmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        result = fw._format_event("deleted", "/tmp/test.py", None)
        self.assertIn("test.py", result)
        self.assertIn("deleted", result)

    def test_format_event_moved(self):
        """_format_event tasinma olayini dogru bicimlendirmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        result = fw._format_event("moved", "/tmp/test.py", "/tmp/test2.py")
        self.assertIn("test.py", result)
        self.assertIn("test2.py", result)

    def test_get_recent_events_empty(self):
        """get_recent_events baslangicta bos liste dondurmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        events = fw.get_recent_events()
        self.assertEqual(events, [])

    def test_get_recent_events_limit(self):
        """get_recent_events limit ile calismali."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        events = fw.get_recent_events(limit=5)
        self.assertIsInstance(events, list)

    def test_on_event_created(self):
        """_on_event created tipini dogru kaydetmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("created", "/tmp/test_created.py", None)
        events = fw.get_recent_events()
        self.assertGreaterEqual(len(events), 1)
        self.assertIn("test_created.py", events[0].get("filename", ""))

    def test_on_event_modified(self):
        """_on_event modified tipini dogru kaydetmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("modified", "/tmp/test_modified.py", None)
        events = fw.get_recent_events()
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "modified")

    def test_on_event_deleted(self):
        """_on_event deleted tipini dogru kaydetmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("deleted", "/tmp/test_deleted.py", None)
        events = fw.get_recent_events()
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "deleted")

    def test_on_event_moved(self):
        """_on_event moved tipini dest_path ile kaydetmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("moved", "/tmp/test.py", "/tmp/test2.py")
        events = fw.get_recent_events()
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "moved")
        self.assertEqual(events[0]["dest"], "/tmp/test2.py")

    def test_get_event_summary_empty(self):
        """get_event_summary event yokken mesaj dondurmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        summary = fw.get_event_summary(seconds=60)
        self.assertIn("değişiklik yok", summary)

    def test_get_event_summary_with_events(self):
        """get_event_summary event varken istatistik dondurmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("created", "/tmp/a.py", None)
        fw._on_event("modified", "/tmp/b.py", None)
        summary = fw.get_event_summary(seconds=3600)
        self.assertIn("Oluşturuldu", summary)
        self.assertIn("Değişti", summary)

    def test_start_stop(self):
        """start() ve stop() calisabilmeli."""
        from actions.watchdog.file_watcher import FileWatcher
        with TemporaryDirectory() as tmpdir:
            fw = FileWatcher([tmpdir])
            fw.start()
            self.assertTrue(fw._running)
            fw.stop()
            self.assertFalse(fw._running)

    def test_event_handler_on_created(self):
        """JARVISEventHandler.on_created dogru callback cagirmali."""
        from actions.watchdog.file_watcher import JARVISEventHandler
        events = []
        def cb(etype, src, dest):
            events.append((etype, src, dest))
        handler = JARVISEventHandler(cb)

        class MockEvent:
            is_directory = False
            src_path = "/tmp/test_handler.py"

        handler.on_created(MockEvent())
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0][0], "created")
        self.assertEqual(events[0][1], "/tmp/test_handler.py")

    def test_event_handler_on_deleted(self):
        """JARVISEventHandler.on_deleted dogru callback cagirmali."""
        from actions.watchdog.file_watcher import JARVISEventHandler
        events = []
        def cb(etype, src, dest):
            events.append((etype, src, dest))
        handler = JARVISEventHandler(cb)

        class MockEvent:
            is_directory = False
            src_path = "/tmp/test_del.py"

        handler.on_deleted(MockEvent())
        self.assertEqual(events[0][0], "deleted")

    def test_event_handler_on_modified(self):
        """JARVISEventHandler.on_modified dogru callback cagirmali."""
        from actions.watchdog.file_watcher import JARVISEventHandler
        events = []
        def cb(etype, src, dest):
            events.append((etype, src, dest))
        handler = JARVISEventHandler(cb)

        class MockEvent:
            is_directory = False
            src_path = "/tmp/test_mod.py"

        handler.on_modified(MockEvent())
        self.assertEqual(events[0][0], "modified")

    def test_event_handler_on_moved(self):
        """JARVISEventHandler.on_moved dogru callback cagirmali."""
        from actions.watchdog.file_watcher import JARVISEventHandler
        events = []
        def cb(etype, src, dest):
            events.append((etype, src, dest))
        handler = JARVISEventHandler(cb)

        class MockEvent:
            is_directory = False
            src_path = "/tmp/test.py"
            dest_path = "/tmp/test2.py"

        handler.on_moved(MockEvent())
        self.assertEqual(events[0][0], "moved")
        self.assertEqual(events[0][2], "/tmp/test2.py")

    def test_watch_paths_function(self):
        """watch_paths helper FileWatcher dondurmeli."""
        from actions.watchdog.file_watcher import watch_paths, FileWatcher
        watcher = watch_paths(["/tmp"])
        self.assertIsInstance(watcher, FileWatcher)

    def test_debounce_filter(self):
        """Debounce ayni dosyaya gelen eventi 2 sn icinde filtrelemeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("created", "/tmp/debounce_test.py", None)
        fw._on_event("modified", "/tmp/debounce_test.py", None)
        events = fw.get_recent_events()
        self.assertEqual(len(events), 1)

    def test_event_data_structure(self):
        """_on_event kaydettigi event dict dogru anahtarlari icermeli."""
        from actions.watchdog.file_watcher import FileWatcher
        fw = FileWatcher(["/tmp"])
        fw._on_event("created", "/tmp/struct_test.py", None)
        events = fw.get_recent_events()
        self.assertIn("type", events[0])
        self.assertIn("src", events[0])
        self.assertIn("time", events[0])
        self.assertIn("filename", events[0])
        self.assertEqual(events[0]["filename"], "struct_test.py")


if __name__ == "__main__":
    unittest.main(verbosity=2)
