from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ui.sound_manager import SoundManager

BASE_DIR = Path(__file__).resolve().parent.parent


class TestSoundManagerExtended(unittest.TestCase):
    """SoundManager threading/subprocess/metot testleri — mock ile."""

    def setUp(self):
        from ui.sound_manager import SoundManager
        self.sm = SoundManager()
        self.sm._enabled = True

    def test_init_basic(self):
        """__init__ tum alanlari dogru baslatmali."""
        self.assertTrue(self.sm._enabled)
        self.assertEqual(self.sm._volume, 0.20)
        self.assertIsNone(self.sm._ambient_proc)
        self.assertIsNone(self.sm._ambient_stop)
        self.assertIsNone(self.sm._foreground_proc)
        self.assertEqual(self.sm._foreground_tag, "")

    @patch("ui.sound_manager.play_audio_file")
    def test_start_audio(self, mock_play):
        """_start_audio play_audio_file cagirip process'i kaydetmeli."""
        from pathlib import Path
        mock_proc = MagicMock()
        mock_play.return_value = mock_proc

        proc = self.sm._start_audio(Path("/tmp/test.mp3"), 0.5)
        self.assertEqual(proc, mock_proc)
        mock_play.assert_called_once()
        self.assertIn(mock_proc, self.sm._all_sound_procs)

    def test_forget_process(self):
        """_forget_process process'i set'ten cikarmali."""
        proc = MagicMock()
        self.sm._all_sound_procs.add(proc)
        self.assertIn(proc, self.sm._all_sound_procs)
        self.sm._forget_process(proc)
        self.assertNotIn(proc, self.sm._all_sound_procs)

    def test_forget_process_none(self):
        """_forget_process None ile hata firlatmamali."""
        self.sm._forget_process(None)  # should not raise

    @patch("ui.sound_manager.os.killpg")
    @patch("ui.sound_manager.os.getpgid")
    def test_terminate_process(self, mock_getpgid, mock_killpg):
        """_terminate_process SIGTERM gonderip beklemeli."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # hala calisiyor
        mock_getpgid.return_value = 12345

        self.sm._terminate_process(mock_proc)
        mock_killpg.assert_called_once_with(12345, 15)  # SIGTERM

    def test_terminate_process_none(self):
        """_terminate_process None ile hata firlatmamali."""
        self.sm._terminate_process(None)

    def test_terminate_process_already_done(self):
        """_terminate_process process zaten bitmisse atlamali."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        self.sm._terminate_process(mock_proc)
        mock_proc.terminate.assert_not_called()

    @patch("ui.sound_manager.IS_WINDOWS", True)
    @patch("pathlib.Path.exists", return_value=True)
    @patch.object(SoundManager, "_start_audio", return_value=MagicMock())
    @patch.object(SoundManager, "_loop_ambient")
    def test_start_ambient_windows(self, mock_loop, mock_start, mock_exists):
        """start_ambient Windows'ta ambient loop baslatmali."""
        self.sm.start_ambient()
        self.assertIsNotNone(self.sm._ambient_stop)
        self.assertIsNotNone(self.sm._ambient_thread)

    @patch("ui.sound_manager.IS_WINDOWS", False)
    def test_start_ambient_linux(self):
        """start_ambient Linux'ta hicbir sey yapmamali."""
        self.sm.start_ambient()
        self.assertIsNone(self.sm._ambient_stop)

    def test_toggle(self):
        """toggle _enabled'i tersine cevirmeli."""
        initial = self.sm._enabled
        result = self.sm.toggle()
        self.assertEqual(result, not initial)
        self.assertEqual(self.sm._enabled, not initial)

    def test_set_volume_clamp_low(self):
        """set_volume negatif degeri 0'a kilitler."""
        self.sm.set_volume(-1.0)
        self.assertEqual(self.sm._volume, 0.0)

    def test_set_volume_clamp_high(self):
        """set_volume 1'den buyuk degeri 1'e kilitler."""
        self.sm.set_volume(2.0)
        self.assertEqual(self.sm._volume, 1.0)

    def test_set_volume_normal(self):
        """set_volume normal degeri korur."""
        self.sm.set_volume(0.5)
        self.assertAlmostEqual(self.sm._volume, 0.5)

    def test_stop_all(self):
        """stop_all tum process'leri temizlemeli ve _enabled=False yapmali."""
        mock_proc = MagicMock()
        self.sm._all_sound_procs.add(mock_proc)
        self.sm._ambient_proc = mock_proc
        self.sm._ambient_stop = MagicMock()
        self.sm._foreground_proc = mock_proc
        self.sm._foreground_stop = MagicMock()
        self.sm._foreground_tag = "think"

        self.sm.stop_all()

        self.assertFalse(self.sm._enabled)
        self.assertIsNone(self.sm._ambient_stop)
        self.assertIsNone(self.sm._ambient_proc)
        self.assertIsNone(self.sm._foreground_stop)
        self.assertIsNone(self.sm._foreground_proc)
        self.assertEqual(self.sm._foreground_tag, "")
        self.assertEqual(len(self.sm._all_sound_procs), 0)

    @patch("ui.sound_manager.IS_WINDOWS", True)
    @patch("ui.sound_manager._START_FILE", MagicMock())
    @patch.object(SoundManager, "_play_foreground")
    def test_play_startup(self, mock_play):
        """play_startup _play_foreground cagirmali."""
        self.sm.play_startup()
        mock_play.assert_called_once()

    @patch("ui.sound_manager.IS_WINDOWS", True)
    @patch("ui.sound_manager._DONE_FILE", MagicMock())
    @patch.object(SoundManager, "_play_foreground")
    def test_play_success(self, mock_play):
        """play_success _play_foreground cagirmali."""
        self.sm.play_success()
        mock_play.assert_called_once()

    @patch("ui.sound_manager.IS_WINDOWS", True)
    @patch("ui.sound_manager._ERROR_FILE", MagicMock())
    @patch.object(SoundManager, "_play_foreground")
    def test_play_error(self, mock_play):
        """play_error _play_foreground cagirmali."""
        self.sm.play_error()
        mock_play.assert_called_once()

    @patch("ui.sound_manager.IS_WINDOWS", True)
    @patch("ui.sound_manager._THINK_FILE", MagicMock())
    @patch.object(SoundManager, "_play_foreground")
    def test_start_thinking(self, mock_play):
        """start_thinking _play_foreground loop=True ile cagirmali."""
        self.sm.start_thinking()
        mock_play.assert_called_once()

    def test_stop_thinking_no_think(self):
        """stop_thinking _foreground_tag think degilse durdurmamali."""
        self.sm._foreground_tag = "startup"
        with patch.object(self.sm, "_stop_foreground") as mock_stop:
            self.sm.stop_thinking()
            mock_stop.assert_not_called()

    def test_stop_thinking_is_think(self):
        """stop_thinking _foreground_tag think ise durdurma cagirmali."""
        self.sm._foreground_tag = "think"
        with patch.object(self.sm, "_stop_foreground") as mock_stop:
            self.sm.stop_thinking()
            mock_stop.assert_called_once()

    def test_get_volume(self):
        """get_volume dogru degeri dondurmeli."""
        self.sm._volume = 0.75
        self.assertEqual(self.sm.get_volume(), 0.75)


class TestSoundManagerWithMockedProcess(unittest.TestCase):
    """_play_foreground ve _foreground_worker testleri."""

    def setUp(self):
        from ui.sound_manager import SoundManager
        self.sm = SoundManager()

    def test_play_foreground_proc_none_initially(self):
        """_foreground_proc baslangicta None olmali."""
        self.assertIsNone(self.sm._foreground_proc)
        self.assertIsNone(self.sm._foreground_stop)
        self.assertEqual(self.sm._foreground_tag, "")

    @patch("ui.sound_manager.IS_WINDOWS", False)
    def test_play_foreground_linux(self):
        """_play_foreground Linux'ta hicbir sey yapmamali."""
        from pathlib import Path
        self.sm._play_foreground(Path("/tmp/test.mp3"), "test")
        self.assertIsNone(self.sm._foreground_stop)


if __name__ == "__main__":
    unittest.main(verbosity=2)
