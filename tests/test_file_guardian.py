"""
File Guardian birim testleri.
"""
from __future__ import annotations


import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from actions.file_guardian import find_large_files, get_folder_summary, cleanup_folder


class TestFileGuardian(unittest.TestCase):

    @patch("actions.file_guardian.os.walk")
    @patch("pathlib.Path.stat")
    def test_find_large_files(self, mock_stat, mock_walk):
        """Büyük dosya arama."""
        mock_walk.return_value = [
            ("/home/user", [], ["bigfile.zip", "small.txt"])
        ]
        mock_stat.return_value = MagicMock(st_size=200*1024*1024)  # 200MB

        result = find_large_files("/home/user", 100, 10)
        self.assertIn("BÜYÜK DOSYALAR", result)
        self.assertIn("bigfile.zip", result)
        self.assertIn("200.0MB", result)

    @patch("actions.file_guardian.os.walk")
    def test_find_large_files_empty(self, mock_walk):
        """Büyük dosya bulunamadı."""
        mock_walk.return_value = []

        result = find_large_files("/empty", 100, 10)
        self.assertIn("bulunamadı", result)

    @patch("actions.file_guardian.os.walk")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.is_file")
    def test_find_large_files_limit(self, mock_isfile, mock_stat, mock_walk):
        """Limit kontrolü."""
        mock_walk.return_value = [
            ("/home/user", [], [f"file{i}.zip" for i in range(30)])
        ]
        mock_stat.return_value = MagicMock(st_size=150*1024*1024)
        mock_isfile.return_value = True

        result = find_large_files("/home/user", 100, 5)
        # Sadece 5 dosya gösterilmeli
        lines = result.split("\n")
        file_lines = [l for l in lines if "file" in l]
        self.assertLessEqual(len(file_lines), 5)

    @patch("pathlib.Path.rglob")
    @patch("pathlib.Path.exists")
    def test_get_folder_summary(self, mock_exists, mock_rglob):
        """Klasör özet istatistikleri."""
        file1 = MagicMock(spec=Path)
        file1.is_file.return_value = True
        file1.is_dir.return_value = False
        file1.suffix = ".txt"
        file1.stat.return_value = MagicMock(st_size=1024*1024)

        file2 = MagicMock(spec=Path)
        file2.is_file.return_value = True
        file2.is_dir.return_value = False
        file2.suffix = ".pdf"
        file2.stat.return_value = MagicMock(st_size=1024*1024)

        file3 = MagicMock(spec=Path)
        file3.is_file.return_value = True
        file3.is_dir.return_value = False
        file3.suffix = ".jpg"
        file3.stat.return_value = MagicMock(st_size=1024*1024)

        dir1 = MagicMock(spec=Path)
        dir1.is_file.return_value = False
        dir1.is_dir.return_value = True

        mock_exists.return_value = True
        mock_rglob.return_value = [file1, file2, dir1, file3]

        result = get_folder_summary("/home/user/docs")
        self.assertIn("KLASÖR ÖZETİ", result)
        self.assertIn("3", result)  # 3 dosya
        self.assertIn("1", result)  # 1 klasör

    @patch("pathlib.Path.rglob")
    @patch("pathlib.Path.exists")
    def test_cleanup_folder_dry_run(self, mock_exists, mock_rglob):
        """Dry run temizlik."""
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.name = "temp.tmp"
        mock_file.stat.return_value = MagicMock(st_size=1024)
        mock_file.__str__ = lambda s: "/tmp/temp.tmp"
        mock_exists.return_value = True
        mock_rglob.return_value = [mock_file]

        result = cleanup_folder("/tmp", "*.tmp", True)
        self.assertIn("DRY RUN", result)
        self.assertIn("temp.tmp", result)

    def test_cleanup_folder_not_found(self):
        """Bulunamayan klasör."""
        result = cleanup_folder("/nonexistent", "*", True)
        self.assertIn("bulunamadı", result)


if __name__ == "__main__":
    unittest.main()
