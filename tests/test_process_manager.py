"""
Process Manager birim testleri.
"""
from __future__ import annotations


import unittest
from unittest.mock import patch, MagicMock
import psutil

from actions.process_manager import list_processes, kill_process, set_process_priority, find_process_by_port


class TestProcessManager(unittest.TestCase):

    @patch("actions.process_manager.psutil.process_iter")
    def test_list_processes_by_cpu(self, mock_iter):
        """CPU'ya göre süreç listeleme."""
        mock_procs = [
            MagicMock(info={"pid": 1, "name": "chrome", "cpu_percent": 25.0, "memory_percent": 10.0}),
            MagicMock(info={"pid": 2, "name": "spotify", "cpu_percent": 5.0, "memory_percent": 3.0}),
            MagicMock(info={"pid": 3, "name": "code", "cpu_percent": 15.0, "memory_percent": 8.0}),
        ]
        mock_iter.return_value = mock_procs

        result = list_processes("cpu", 10)
        self.assertIn("ÇALIŞAN SÜREÇLER", result)
        self.assertIn("chrome", result)
        self.assertIn("spotify", result)
        self.assertIn("code", result)

    @patch("actions.process_manager.psutil.process_iter")
    def test_list_processes_by_memory(self, mock_iter):
        """RAM'e göre süreç listeleme."""
        mock_procs = [
            MagicMock(info={"pid": 1, "name": "chrome", "cpu_percent": 5.0, "memory_percent": 30.0}),
            MagicMock(info={"pid": 2, "name": "firefox", "cpu_percent": 3.0, "memory_percent": 20.0}),
        ]
        mock_iter.return_value = mock_procs

        result = list_processes("memory", 5)
        self.assertIn("chrome", result)
        self.assertIn("30.0", result)

    @patch("actions.process_manager.psutil.Process")
    def test_kill_process_by_pid(self, mock_process_class):
        """PID ile süreç öldürme."""
        mock_proc = MagicMock()
        mock_proc.name.return_value = "chrome"
        mock_proc.terminate = MagicMock()
        mock_proc.wait = MagicMock()
        mock_process_class.return_value = mock_proc

        result = kill_process("1234", False)
        self.assertIn("chrome", result)
        self.assertIn("düzgün", result)
        mock_proc.terminate.assert_called_once()

    @patch("actions.process_manager.psutil.Process")
    def test_kill_process_force(self, mock_process_class):
        """Zorla süreç öldürme."""
        mock_proc = MagicMock()
        mock_proc.name.return_value = "spotify"
        mock_proc.kill = MagicMock()
        mock_process_class.return_value = mock_proc

        result = kill_process("5678", True)
        self.assertIn("zorla", result)
        mock_proc.kill.assert_called_once()

    def test_kill_process_not_found(self):
        """Bulunamayan süreç."""
        with patch("actions.process_manager.psutil.Process") as mock_process:
            mock_process.side_effect = psutil.NoSuchProcess(9999)
            result = kill_process("9999", False)
            self.assertIn("bulunamadı", result)

    def test_kill_process_access_denied(self):
        """Erişim reddedilen süreç."""
        with patch("actions.process_manager.psutil.Process") as mock_process:
            mock_process.side_effect = psutil.AccessDenied()
            result = kill_process("1", False)
            self.assertIn("yetki", result)

    @patch("actions.process_manager.psutil.Process")
    def test_set_process_priority(self, mock_process_class):
        """Süreç önceliği ayarlama."""
        mock_proc = MagicMock()
        mock_proc.name.return_value = "game"
        mock_proc.nice = MagicMock()
        mock_process_class.return_value = mock_proc

        result = set_process_priority("1234", "high")
        self.assertIn("high", result)
        self.assertIn("game", result)
        mock_proc.nice.assert_called_once()

    def test_set_process_invalid_priority(self):
        """Geçersiz öncelik."""
        result = set_process_priority("1234", "ultra")
        self.assertIn("Geçersiz", result)

    @patch("actions.process_manager.psutil.net_connections")
    def test_find_process_by_port(self, mock_connections):
        """Port kullanan süreç bulma."""
        mock_conn = MagicMock()
        mock_conn.laddr = MagicMock(port=8080)
        mock_conn.pid = 1234
        mock_connections.return_value = [mock_conn]

        with patch("actions.process_manager.psutil.Process") as mock_process:
            mock_proc = MagicMock()
            mock_proc.name.return_value = "node"
            mock_process.return_value = mock_proc

            result = find_process_by_port(8080)
            self.assertIn("8080", result)
            self.assertIn("node", result)

    @patch("actions.process_manager.psutil.net_connections")
    def test_find_process_by_port_empty(self, mock_connections):
        """Boş port."""
        mock_connections.return_value = []

        result = find_process_by_port(9999)
        self.assertIn("kullanımda değil", result)


if __name__ == "__main__":
    unittest.main()
