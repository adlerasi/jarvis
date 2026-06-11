"""
Network Monitor birim testleri.
"""
from __future__ import annotations


import unittest
from unittest.mock import patch, MagicMock

from actions.network_monitor import get_network_summary, ping_host


class TestNetworkMonitor(unittest.TestCase):

    @patch("actions.network_monitor.psutil.net_if_addrs")
    @patch("actions.network_monitor.psutil.net_io_counters")
    def test_get_network_summary(self, mock_io, mock_addrs):
        """Ağ özet raporu."""
        mock_addrs.return_value = {
            "Wi-Fi": [MagicMock(family=2, address="192.168.1.100")],
            "Ethernet": [MagicMock(family=2, address="10.0.0.50")],
        }
        mock_io.return_value = MagicMock(
            bytes_sent=1*1024**3, bytes_recv=512*1024**3,
            errout=0, errin=0
        )

        result = get_network_summary()
        self.assertIn("AĞ ÖZETİ", result)
        self.assertIn("192.168.1.100", result)
        self.assertIn("1.00GB", result)  # Gönderilen

    @patch("actions.network_monitor.psutil.net_if_addrs")
    @patch("actions.network_monitor.psutil.net_io_counters")
    def test_get_network_summary_empty(self, mock_io, mock_addrs):
        """Boş ağ arayüzü."""
        mock_addrs.return_value = {}
        mock_io.return_value = MagicMock(bytes_sent=0, bytes_recv=0, errout=0, errin=0)

        result = get_network_summary()
        self.assertIn("Toplam trafik", result)

    @patch("subprocess.run")
    def test_ping_host_success(self, mock_run):
        """Başarılı ping."""
        mock_run.return_value = MagicMock(
            stdout="Pinging google.com [142.250.185.78] with 32 bytes of data:\nReply from 142.250.185.78: bytes=32 time=15ms TTL=117",
            returncode=0
        )

        result = ping_host("google.com", 4)
        self.assertIn("google.com", result)

    @patch("subprocess.run")
    def test_ping_host_timeout(self, mock_run):
        """Ping zaman aşımı."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("ping", 30)

        result = ping_host("unreachable.host", 4)
        self.assertIn("zaman aşımı", result)

    @patch("subprocess.run")
    def test_ping_host_error(self, mock_run):
        """Ping hatası."""
        mock_run.side_effect = FileNotFoundError("ping not found")

        result = ping_host("google.com", 4)
        self.assertIn("hatası", result)


if __name__ == "__main__":
    unittest.main()
