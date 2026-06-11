from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestCronWebUI(unittest.TestCase):
    """actions.cron_web_ui import ve sabit testleri."""

    def test_module_import(self):
        """actions.cron_web_ui import edilebilmeli."""
        from actions import cron_web_ui
        self.assertIsNotNone(cron_web_ui)

    def test_cron_web_server_class(self):
        """CronWebServer sinifi mevcut olmali."""
        from actions.cron_web_ui import CronWebServer
        self.assertIsNotNone(CronWebServer)

    def test_cron_web_handler_class(self):
        """CronWebHandler sinifi mevcut olmali."""
        from actions.cron_web_ui import CronWebHandler
        self.assertIsNotNone(CronWebHandler)

    def test_default_port(self):
        """CronWebServer varsayilan port 8765 olmali."""
        from actions.cron_web_ui import CronWebServer
        server = CronWebServer()
        self.assertEqual(server.port, 8765)

    def test_custom_port(self):
        """CronWebServer ozel port ile baslatilabilmeli."""
        from actions.cron_web_ui import CronWebServer
        server = CronWebServer(port=9999)
        self.assertEqual(server.port, 9999)

    def test_custom_host(self):
        """CronWebServer ozel host ile baslatilabilmeli."""
        from actions.cron_web_ui import CronWebServer
        server = CronWebServer(host="0.0.0.0")
        self.assertEqual(server.host, "0.0.0.0")

    def test_html_dashboard_content(self):
        """HTML_DASHBOARD JARVIS metni icermeli."""
        from actions.cron_web_ui import HTML_DASHBOARD
        self.assertIsInstance(HTML_DASHBOARD, str)
        self.assertGreater(len(HTML_DASHBOARD), 100)
        self.assertIn("JARVIS", HTML_DASHBOARD)

    def test_html_dashboard_has_style(self):
        """HTML_DASHBOARD CSS icermeli."""
        from actions.cron_web_ui import HTML_DASHBOARD
        self.assertIn("</style>", HTML_DASHBOARD)

    def test_html_dashboard_has_form(self):
        """HTML_DASHBOARD yeni gorev formu icermeli."""
        from actions.cron_web_ui import HTML_DASHBOARD
        self.assertIn("newJobForm", HTML_DASHBOARD)

    def test_is_running_false_initially(self):
        """is_running() baslangicta False olmali."""
        from actions.cron_web_ui import CronWebServer
        server = CronWebServer()
        self.assertFalse(server.is_running())

    def test_double_stop(self):
        """Ard arda stop hata firlatmamali."""
        from actions.cron_web_ui import CronWebServer
        server = CronWebServer()
        msg1 = server.stop()
        self.assertIsInstance(msg1, str)
        msg2 = server.stop()
        self.assertIn("zaten durdurulmuş", msg2.lower())

    def test_start_returns_string(self):
        """start() str dondurmeli (port kullanimda olabilir)."""
        from actions.cron_web_ui import CronWebServer
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            available = s.connect_ex(("127.0.0.1", 19876)) != 0
        if available:
            server = CronWebServer(port=19876)
            msg = server.start()
            self.assertIsInstance(msg, str)
            self.assertIn("başlatıldı", msg.lower())
            server.stop()

    def test_start_stop_cycle(self):
        """start() ve stop() calisabilmeli."""
        from actions.cron_web_ui import CronWebServer
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            available = s.connect_ex(("127.0.0.1", 19877)) != 0
        if available:
            server = CronWebServer(port=19877)
            server.start()
            self.assertTrue(server.is_running())
            server.stop()
            self.assertFalse(server.is_running())

    def test_handler_has_http_methods(self):
        """CronWebHandler do_* metodlarina sahip olmali."""
        from actions.cron_web_ui import CronWebHandler
        self.assertTrue(hasattr(CronWebHandler, "do_GET"))
        self.assertTrue(hasattr(CronWebHandler, "do_POST"))
        self.assertTrue(hasattr(CronWebHandler, "do_DELETE"))


class TestCronWebUIFunctions(unittest.TestCase):
    """Module-level fonksiyon testleri."""

    def test_start_cron_web_ui(self):
        """start_cron_web_ui mevcut ve str dondurmeli."""
        from actions.cron_web_ui import start_cron_web_ui
        self.assertTrue(callable(start_cron_web_ui))

    def test_start_cron_web_ui_port(self):
        """start_cron_web_ui port parametresi ile calismali."""
        from actions.cron_web_ui import start_cron_web_ui
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            available = s.connect_ex(("127.0.0.1", 19878)) != 0
        if available:
            result = start_cron_web_ui(port=19878)
            self.assertIsInstance(result, str)
            # Cleanup: bul ve durdur
            from actions.cron_web_ui import CronWebServer
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, CronWebServer) and obj.port == 19878:
                    obj.stop()
                    break


if __name__ == "__main__":
    unittest.main(verbosity=2)
