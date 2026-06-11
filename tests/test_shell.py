from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

try:
    import pyaudio  # noqa: F401
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    from google import genai  # noqa: F401
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestShell(unittest.TestCase):
    """shell modulu — guvenlik filtreleme + validation testleri."""

    def setUp(self):
        from actions import shell
        self.mod = shell

    def test_shell_run_empty(self):
        """shell_run bos komutla hata doner."""
        result = self.mod.shell_run("")
        self.assertIn("belirtilmedi", result)

    def test_shell_run_none(self):
        """shell_run None ile hata doner."""
        result = self.mod.shell_run(None)
        self.assertIn("belirtilmedi", result)

    def test_shell_run_blocked_shutdown(self):
        """shell_run shutdown komutunu engeller."""
        result = self.mod.shell_run("shutdown -s -t 0")
        self.assertIn("engellendi", result)

    def test_shell_run_blocked_rm_rf(self):
        """shell_run rm -rf komutunu engeller (dangerous prefix cakar)."""
        result = self.mod.shell_run("rm -rf /")
        # "rm " ile basladigi icin dangerous prefix kontrolune takilir
        self.assertIn("G\xfcvenlik", result)  # Güvenlik (umlaut)

    def test_shell_run_blocked_dd(self):
        """shell_run dd if= komutunu engeller."""
        result = self.mod.shell_run("dd if=/dev/sda of=/dev/null")
        self.assertIn("engellendi", result)

    def test_shell_run_dangerous_prefix_rm(self):
        """shell_run rm ile baslayan komutlari engeller."""
        result = self.mod.shell_run("rm myfile.txt")
        self.assertIn("G\xfcvenlik", result)  # Güvenlik (umlaut'lu u)

    def test_shell_run_dangerous_prefix_sudo(self):
        """shell_run sudo ile baslayan komutlari engeller."""
        result = self.mod.shell_run("sudo apt install")
        self.assertIn("G\xfcvenlik", result)

    def test_shell_run_normal_echo(self):
        """shell_run normal komut calistirir."""
        result = self.mod.shell_run("echo test123")
        self.assertIn("test123", result)

    def test_blocked_list_not_empty(self):
        """BLOCKED listesi bos degil."""
        self.assertGreater(len(self.mod.BLOCKED), 0)

    def test_blocked_list_all_strings(self):
        """BLOCKED listesindeki her sey string."""
        for item in self.mod.BLOCKED:
            self.assertIsInstance(item, str)


# =============================================================================
# 17. WHATSAPP — SAF FONKSIYON TESTLERI
# =============================================================================
