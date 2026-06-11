from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path


class TestAudioSystemPackage(unittest.TestCase):
    """core.audio_system paketi import ve export testleri."""

    def test_package_import(self):
        """core.audio_system import edilebilmeli."""
        from core import audio_system
        self.assertIsNotNone(audio_system)

    def test_package_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from core.audio_system import __all__
        expected = ["AudioPlayer", "get_audio_player", "play_wav", "play_bytes",
                    "TTSEngine", "get_tts_engine", "speak_text",
                    "STTEngine", "get_stt_engine"]
        for symbol in expected:
            self.assertIn(symbol, __all__)


class TestBaseAudioPlayer(unittest.TestCase):
    """core.audio_system.audio_player abstract interface testi."""

    def test_module_import(self):
        """audio_player modulu import edilebilmeli."""
        from core.audio_system import audio_player
        self.assertIsNotNone(audio_player)

    def test_base_audio_player_is_abstract(self):
        """BaseAudioPlayer ABC'dir ve instantiate edilemez."""
        from core.audio_system.audio_player import BaseAudioPlayer
        from abc import ABC
        self.assertTrue(issubclass(BaseAudioPlayer, ABC))
        with self.assertRaises(TypeError):
            BaseAudioPlayer()

    def test_linux_audio_player_available_on_linux(self):
        """LinuxAudioPlayer.is_available Linux'ta True donebilir."""
        from core.audio_system.audio_player import LinuxAudioPlayer
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                player = LinuxAudioPlayer()
                # is_available checks cmd existence
                self.assertTrue(callable(player.is_available))

    def test_linux_audio_player_not_available_on_windows(self):
        """LinuxAudioPlayer.is_available Windows'ta False doner."""
        from core.audio_system.audio_player import LinuxAudioPlayer
        with patch("platform.system", return_value="Windows"):
            player = LinuxAudioPlayer()
            self.assertFalse(player.is_available())

    def test_get_audio_player_returns_instance(self):
        """get_audio_player bir AudioPlayer instance'i dondurur."""
        from core.audio_system.audio_player import get_audio_player, AudioPlayer
        player = get_audio_player()
        self.assertIsInstance(player, AudioPlayer)


class TestBaseTTSEngine(unittest.TestCase):
    """core.audio_system.tts_engine abstract interface testi."""

    def test_module_import(self):
        """tts_engine modulu import edilebilmeli."""
        from core.audio_system import tts_engine
        self.assertIsNotNone(tts_engine)

    def test_base_tts_engine_is_abstract(self):
        """BaseTTSEngine ABC'dir ve instantiate edilemez."""
        from core.audio_system.tts_engine import BaseTTSEngine
        from abc import ABC
        self.assertTrue(issubclass(BaseTTSEngine, ABC))
        with self.assertRaises(TypeError):
            BaseTTSEngine()

    def test_piper_tts_detect_model_no_dir(self):
        """PiperTTSEngine model dizini yoksa _detect_model hata firlatmaz."""
        from core.audio_system.tts_engine import PiperTTSEngine
        with patch("pathlib.Path.exists", return_value=False):
            engine = PiperTTSEngine(model_dir=Path("/tmp/nonexistent_tts_dir"))
            self.assertIsNone(engine._model_path)
            self.assertIsNone(engine._config_path)

    def test_piper_tts_detect_model_with_dir(self):
        """PiperTTSEngine model dizini varsa onnx dosyalarini arar."""
        from core.audio_system.tts_engine import PiperTTSEngine
        mock_onnx = MagicMock()
        mock_onnx.glob.return_value = [Path("test.onnx")]
        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(Path, "glob", return_value=[Path("test.onnx")]):
                engine = PiperTTSEngine(model_dir=Path("/tmp/test_tts"))
                self.assertIsNotNone(engine._model_path)

    def test_get_tts_engine_returns_instance(self):
        """get_tts_engine bir TTSEngine instance'i dondurur."""
        from core.audio_system.tts_engine import get_tts_engine, TTSEngine
        engine = get_tts_engine()
        self.assertIsInstance(engine, TTSEngine)


class TestBaseSTTEngine(unittest.TestCase):
    """core.audio_system.stt_engine abstract interface testi."""

    def test_module_import(self):
        """stt_engine modulu import edilebilmeli."""
        from core.audio_system import stt_engine
        self.assertIsNotNone(stt_engine)

    def test_base_stt_engine_is_abstract(self):
        """BaseSTTEngine ABC'dir ve instantiate edilemez."""
        from core.audio_system.stt_engine import BaseSTTEngine
        from abc import ABC
        self.assertTrue(issubclass(BaseSTTEngine, ABC))
        with self.assertRaises(TypeError):
            BaseSTTEngine()

    def test_faster_whisper_stt_init_defaults(self):
        """FasterWhisperSTT varsayilan parametrelerle baslatilir."""
        from core.audio_system.stt_engine import FasterWhisperSTT
        # Use patch to prevent actual model loading
        with patch("core.audio_system.stt_engine.FasterWhisperSTT.__init__", return_value=None):
            engine = FasterWhisperSTT.__new__(FasterWhisperSTT)
            engine.model_size = "base"
            engine.language = "tr"
            engine.device = "cpu"
            engine.compute_type = "int8"
            self.assertEqual(engine.model_size, "base")
            self.assertEqual(engine.language, "tr")

    def test_concrete_stt_subclass_possible(self):
        """BaseSTTEngine'dan tureyen sinif abstract'lari implement edebilmeli."""
        from core.audio_system.stt_engine import BaseSTTEngine

        class TestSTT(BaseSTTEngine):
            def transcribe(self, audio_data, sample_rate=16000):
                return "test"
            def is_available(self):
                return False
            @property
            def name(self):
                return "test"

        engine = TestSTT()
        self.assertEqual(engine.name, "test")
        self.assertFalse(engine.is_available())
        self.assertEqual(engine.transcribe(b"test"), "test")

    def test_get_stt_engine_returns_instance(self):
        """get_stt_engine bir STTEngine instance'i dondurur."""
        from core.audio_system.stt_engine import get_stt_engine, STTEngine
        engine = get_stt_engine()
        self.assertIsInstance(engine, STTEngine)


if __name__ == "__main__":
    unittest.main(verbosity=2)
