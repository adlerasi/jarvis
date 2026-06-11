"""
System Doctor birim testleri.
"""
from __future__ import annotations


import unittest
from unittest.mock import patch, MagicMock
import psutil

from actions.system_doctor import get_system_health, cleanup_temp_files


class TestSystemDoctor(unittest.TestCase):

    @patch("actions.system_doctor.psutil.disk_partitions")
    @patch("actions.system_doctor.psutil.disk_usage")
    def test_disk_health_normal(self, mock_usage, mock_partitions):
        """Normal disk durumu raporu."""
        mock_partitions.return_value = [
            MagicMock(device="C:\\", mountpoint="C:\\", opts="rw", fstype="NTFS")
        ]
        mock_usage.return_value = MagicMock(
            total=100*1024**3, used=50*1024**3, free=50*1024**3, percent=50.0
        )

        result = get_system_health("disk")
        self.assertIn("DISK SAĞLIĞI", result)
        self.assertIn("50.0GB", result)
        self.assertNotIn("KRİTİK", result)
        self.assertNotIn("UYARI", result)

    @patch("actions.system_doctor.psutil.disk_partitions")
    @patch("actions.system_doctor.psutil.disk_usage")
    def test_disk_health_critical(self, mock_usage, mock_partitions):
        """Kritik disk doluluk raporu."""
        mock_partitions.return_value = [
            MagicMock(device="C:\\", mountpoint="C:\\", opts="rw", fstype="NTFS")
        ]
        mock_usage.return_value = MagicMock(
            total=100*1024**3, used=95*1024**3, free=5*1024**3, percent=95.0
        )

        result = get_system_health("disk")
        self.assertIn("KRİTİK", result)
        self.assertIn("95", result)

    @patch("actions.system_doctor.psutil.disk_partitions")
    @patch("actions.system_doctor.psutil.disk_usage")
    def test_disk_health_warning(self, mock_usage, mock_partitions):
        """Uyarı seviyesi disk doluluk."""
        mock_partitions.return_value = [
            MagicMock(device="D:\\", mountpoint="D:\\", opts="rw", fstype="NTFS")
        ]
        mock_usage.return_value = MagicMock(
            total=500*1024**3, used=420*1024**3, free=80*1024**3, percent=84.0
        )

        result = get_system_health("disk")
        self.assertIn("UYARI", result)
        self.assertNotIn("KRİTİK", result)

    @patch("actions.system_doctor.psutil.virtual_memory")
    def test_memory_health(self, mock_vm):
        """RAM sağlık raporu."""
        mock_vm.return_value = MagicMock(
            total=16*1024**3, used=8*1024**3, percent=50.0, available=8*1024**3
        )

        result = get_system_health("memory")
        self.assertIn("BELLEK SAĞLIĞI", result)
        self.assertIn("8.0GB", result)
        self.assertIn("16.0GB", result)

    @patch("actions.system_doctor.psutil.virtual_memory")
    def test_memory_critical(self, mock_vm):
        """Kritik RAM kullanımı."""
        mock_vm.return_value = MagicMock(
            total=16*1024**3, used=15*1024**3, percent=95.0, available=1*1024**3
        )

        result = get_system_health("memory")
        self.assertIn("KRİTİK", result)

    @patch("actions.system_doctor.psutil.cpu_percent")
    @patch("actions.system_doctor.psutil.cpu_count")
    @patch("actions.system_doctor.psutil.cpu_freq")
    @patch("actions.system_doctor.psutil.process_iter")
    def test_cpu_health(self, mock_procs, mock_freq, mock_count, mock_cpu):
        """CPU sağlık raporu."""
        mock_cpu.return_value = 45.0
        mock_count.return_value = 8
        mock_freq.return_value = MagicMock(current=2400, max=3200)
        mock_procs.return_value = []

        result = get_system_health("cpu")
        self.assertIn("CPU SAĞLIĞI", result)
        self.assertIn("45.0", result)
        self.assertIn("8 çekirdek", result)

    def test_invalid_query(self):
        """Geçersiz sorgu."""
        result = get_system_health("invalid_query")
        self.assertIn("Bilinmeyen sorgu", result)

    def test_all_query(self):
        """'all' sorgusu tüm raporları döndürür."""
        with patch("actions.system_doctor.psutil.disk_partitions") as mock_partitions,              patch("actions.system_doctor.psutil.disk_usage") as mock_usage,              patch("actions.system_doctor.psutil.virtual_memory") as mock_vm,              patch("actions.system_doctor.psutil.cpu_percent") as mock_cpu,              patch("actions.system_doctor.psutil.cpu_count") as mock_count,              patch("actions.system_doctor.psutil.cpu_freq") as mock_freq:

            mock_partitions.return_value = []
            mock_usage.return_value = MagicMock(total=100, used=50, free=50, percent=50)
            mock_vm.return_value = MagicMock(total=16*1024**3, used=8*1024**3, percent=50)
            mock_cpu.return_value = 30.0
            mock_count.return_value = 4
            mock_freq.return_value = MagicMock(current=2000, max=3000)

            result = get_system_health("all")
            self.assertIn("DISK SAĞLIĞI", result)
            self.assertIn("BELLEK SAĞLIĞI", result)
            self.assertIn("CPU SAĞLIĞI", result)

    @patch("actions.system_doctor.os.unlink")
    @patch("actions.system_doctor.os.scandir")
    def test_cleanup_temp_files(self, mock_scandir, mock_unlink):
        """Temp temizliği."""
        mock_entry = MagicMock()
        mock_entry.is_file.return_value = True
        mock_entry.stat.return_value = MagicMock(st_size=1024*1024)
        mock_entry.path = "/tmp/test.txt"
        mock_scandir.return_value = [mock_entry]
        mock_unlink.return_value = None

        result = cleanup_temp_files()
        self.assertIn("temizlendi", result)
        self.assertIn("1 öğe", result)
        self.assertIn("1.0MB", result)


if __name__ == "__main__":
    unittest.main()
