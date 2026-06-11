from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestNetworkAnomalyDetector(unittest.TestCase):
    """NetworkAnomalyDetector pure fonksiyon testleri."""

    def test_module_import(self):
        """actions.network_anomaly import edilebilmeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        self.assertIsNotNone(NetworkAnomalyDetector)

    def test_init(self):
        """__init__ varsayilan degerlerle calismali."""
        from actions.network_anomaly import NetworkAnomalyDetector
        nad = NetworkAnomalyDetector()
        self.assertIsNotNone(nad)

    def test_suspicious_ports(self):
        """SUSPICIOUS_PORTS bilinen C2 portlarini icermeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        ports = NetworkAnomalyDetector.SUSPICIOUS_PORTS
        self.assertIn(4444, ports)
        self.assertIn(31337, ports)
        self.assertIn(12345, ports)
        self.assertIn(27374, ports)

    def test_trusted_domains(self):
        """TRUSTED_DOMAINS guvenilir domainleri icermeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        trusted = NetworkAnomalyDetector.TRUSTED_DOMAINS
        self.assertIn("google.com", trusted)
        self.assertIn("github.com", trusted)
        self.assertIn("cloudflare.com", trusted)

    def test_thresholds(self):
        """Esik deger sabitleri mevcut ve pozitif olmali."""
        from actions.network_anomaly import NetworkAnomalyDetector
        self.assertGreater(NetworkAnomalyDetector.THRESHOLD_CONNECTION_COUNT, 0)
        self.assertGreater(NetworkAnomalyDetector.THRESHOLD_UNIQUE_PORTS, 0)
        self.assertGreater(NetworkAnomalyDetector.THRESHOLD_TOTAL_OUTBOUND, 0)
        self.assertGreater(NetworkAnomalyDetector.THRESHOLD_DNS_PER_PROCESS, 0)

    def test_scan_returns_list(self):
        """scan() en azindan list dondurmeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        nad = NetworkAnomalyDetector()
        result = nad.scan()
        self.assertIsInstance(result, list)

    def test_reset_alerts(self):
        """reset_alerts() alert set'ini temizlemeli ve str dondurmeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        nad = NetworkAnomalyDetector()
        # Once alert ekle
        nad._alerted.add("test_alert")
        self.assertIn("test_alert", nad._alerted)
        result = nad.reset_alerts()
        self.assertIsInstance(result, str)
        self.assertIn("sıfırlandı", result.lower())
        self.assertEqual(len(nad._alerted), 0)

    def test_get_connection_summary(self):
        """get_connection_summary str dondurmeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        nad = NetworkAnomalyDetector()
        result = nad.get_connection_summary()
        self.assertIsInstance(result, str)

    def test_check_ip_reputation(self):
        """check_ip_reputation str dondurmeli."""
        from actions.network_anomaly import NetworkAnomalyDetector
        nad = NetworkAnomalyDetector()
        result = nad.check_ip_reputation("8.8.8.8")
        self.assertIsInstance(result, str)

    def test_connection_history_init(self):
        """__init__'de connection_history ve alerted bos olmali."""
        from actions.network_anomaly import NetworkAnomalyDetector
        nad = NetworkAnomalyDetector()
        self.assertEqual(len(nad._connection_history), 0)
        self.assertEqual(len(nad._alerted), 0)
        self.assertEqual(len(nad._dns_history), 0)


class TestNetworkAnomalyFunctions(unittest.TestCase):
    """Module-level fonksiyon testleri."""

    def test_scan_network_anomalies(self):
        """scan_network_anomalies mevcut ve list dondurmeli."""
        from actions.network_anomaly import scan_network_anomalies
        result = scan_network_anomalies()
        self.assertIsInstance(result, list)

    def test_check_ip(self):
        """check_ip mevcut ve str dondurmeli."""
        from actions.network_anomaly import check_ip
        result = check_ip("8.8.8.8")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
