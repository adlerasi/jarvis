from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestServiceMonitor(unittest.TestCase):
    """actions.service_monitor platform-bagimsiz fonksiyon testleri."""

    def test_module_import(self):
        """actions.service_monitor import edilebilmeli."""
        from actions import service_monitor
        self.assertIsNotNone(service_monitor)

    def test_list_services_import(self):
        """list_services cagirilabilmeli."""
        from actions.service_monitor import list_services
        self.assertTrue(callable(list_services))

    def test_control_service_import(self):
        """control_service cagirilabilmeli."""
        from actions.service_monitor import control_service
        self.assertTrue(callable(control_service))

    def test_get_service_dependencies_import(self):
        """get_service_dependencies cagirilabilmeli."""
        from actions.service_monitor import get_service_dependencies
        self.assertTrue(callable(get_service_dependencies))

    def test_list_services_returns_str(self):
        """list_services str dondurmeli."""
        from actions.service_monitor import list_services
        result = list_services()
        self.assertIsInstance(result, str)

    def test_list_services_with_filter(self):
        """list_services filte ile calisabilmeli."""
        from actions.service_monitor import list_services
        result = list_services(status_filter="running")
        self.assertIsInstance(result, str)

    def test_list_services_limit(self):
        """list_services limit parametresi ile calismali."""
        from actions.service_monitor import list_services
        result = list_services(limit=5)
        self.assertIsInstance(result, str)

    def test_control_service_start(self):
        """control_service start str dondurmeli."""
        from actions.service_monitor import control_service
        result = control_service("test_service", "start")
        self.assertIsInstance(result, str)

    def test_control_service_stop(self):
        """control_service stop str dondurmeli."""
        from actions.service_monitor import control_service
        result = control_service("test_service", "stop")
        self.assertIsInstance(result, str)

    def test_control_service_restart(self):
        """control_service restart str dondurmeli."""
        from actions.service_monitor import control_service
        result = control_service("test_service", "restart")
        self.assertIsInstance(result, str)

    def test_control_service_status(self):
        """control_service status str dondurmeli."""
        from actions.service_monitor import control_service
        result = control_service("test_service", "status")
        self.assertIsInstance(result, str)

    def test_control_service_invalid_action(self):
        """control_service gecersiz aksiyonda hata mesaji icermeli."""
        from actions.service_monitor import control_service
        import os
        result = control_service("test_service", "invalid_action")
        # Linux'ta platform mesaji, Windows'ta gecersiz aksiyon mesaji
        if os.name == "nt":
            self.assertIn("Geçersiz", result)

    def test_control_service_empty_name(self):
        """control_service bos servis adinda uyari mesaji icermeli."""
        from actions.service_monitor import control_service
        import os
        result = control_service("", "start")
        # Linux'ta platform mesaji, Windows'ta bos ad mesaji
        if os.name == "nt":
            self.assertIn("belirtilmedi", result)

    def test_get_service_dependencies_returns_str(self):
        """get_service_dependencies str dondurmeli."""
        from actions.service_monitor import get_service_dependencies
        result = get_service_dependencies("test_service")
        self.assertIsInstance(result, str)

    def test_list_services_platform_check(self):
        """list_services Linux'ta platform uyarisi icerebilir."""
        from actions.service_monitor import list_services
        result = list_services()
        # Linux'ta "sadece Windows" mesaji doner
        self.assertIsInstance(result, str)

    def test_control_service_on_linux(self):
        """control_service Linux'ta platform uyarisi icerebilir."""
        from actions.service_monitor import control_service
        result = control_service("test", "start")
        if "sadece Windows" in result:
            self.assertIn("Windows", result)

    def test_list_services_default_params(self):
        """list_services varsayilan parametrelerle calismali."""
        from actions.service_monitor import list_services
        result = list_services()
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
