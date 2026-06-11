from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestVoiceMemory(unittest.TestCase):
    """memory.voice_memory pure state testleri."""

    def test_module_import(self):
        """memory.voice_memory import edilebilmeli."""
        from memory import voice_memory
        self.assertIsNotNone(voice_memory)

    def test_init_defaults(self):
        """VoiceMemory varsayilan parametrelerle baslatilir."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            self.assertIsNone(vm._current_session)
            self.assertEqual(vm._current_log, [])

    def test_start_session_returns_id(self):
        """start_session session ID dondurur ve log baslatir."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            session_id = vm.start_session()
            self.assertIsNotNone(session_id)
            self.assertTrue(session_id.startswith("session_"))
            self.assertEqual(vm._current_session, session_id)

    def test_start_session_clears_previous_log(self):
        """start_session onceki log'u temizler."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.start_session()
            vm.log_user("test")
            vm.start_session()
            self.assertEqual(vm._current_log, [])

    def test_end_session_no_active_session(self):
        """end_session aktif session yoksa None doner."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            result = vm.end_session()
            self.assertIsNone(result)

    def test_end_session_active_returns_path(self):
        """end_session aktif session varsa dosya yolunu dondurur."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.start_session()
            vm.log_user("test")  # Need at least one log entry for save() to succeed
            with patch("builtins.open", unittest.mock.mock_open()):
                result = vm.end_session()
                self.assertIsNotNone(result)
                self.assertIn("session_", result)

    def test_log_user(self):
        """log_user log'a kullanici kaydi ekler."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.start_session()
            vm.log_user("user_text")
            self.assertEqual(len(vm._current_log), 1)
            entry = vm._current_log[0]
            self.assertEqual(entry["role"], "user")
            self.assertEqual(entry["text"], "user_text")

    def test_log_user_starts_session_if_needed(self):
        """log_user aktif session yokken session baslatir."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.log_user("merhaba")
            self.assertIsNotNone(vm._current_session)
            self.assertEqual(len(vm._current_log), 1)

    def test_get_recent_context_with_log(self):
        """get_recent_context log icerigini dondurur."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.start_session()
            vm.log_user("selam")
            vm.log_jarvis("merhaba")
            context = vm.get_recent_context()
            self.assertIn("selam", context)
            self.assertIn("merhaba", context)

    def test_get_recent_context_no_log(self):
        """get_recent_context aktif session yokken bos string doner."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            self.assertEqual(vm.get_recent_context(), "")

    def test_get_stats_structure(self):
        """get_stats dogru anahtarlara sahip dict doner."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.start_session()
            stats = vm.get_stats()
            self.assertIn("active", stats)
            self.assertIn("current_session", stats)
            self.assertIn("current_turns", stats)
            self.assertTrue(stats["active"])

    def test_clear(self):
        """clear log'u ve session'i temizler."""
        from memory.voice_memory import VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = VoiceMemory(memory_dir=Path("/tmp/test_vm"))
            vm.start_session()
            vm.log_user("test")
            vm.clear()
            self.assertIsNone(vm._current_session)
            self.assertEqual(vm._current_log, [])

    def test_factory_creates_voice_memory(self):
        """create_voice_memory VoiceMemory instance'i dondurur."""
        from memory.voice_memory import create_voice_memory, VoiceMemory
        with patch("pathlib.Path.mkdir"):
            vm = create_voice_memory(memory_dir=Path("/tmp/test_vm"))
            self.assertIsInstance(vm, VoiceMemory)

    def test_module_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from memory.voice_memory import __all__
        self.assertIn("VoiceMemory", __all__)
        self.assertIn("create_voice_memory", __all__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
