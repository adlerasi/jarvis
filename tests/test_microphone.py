from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent


class TestMicrophoneStream(unittest.TestCase):
    """audio.microphone.MicrophoneStream init ve callback testleri."""

    def test_module_import(self):
        """audio.microphone import edilebilmeli."""
        from audio import microphone
        self.assertIsNotNone(microphone)

    @patch("audio.microphone.NoiseSuppressor")
    def test_init_defaults(self, mock_ns):
        """MicrophoneStream varsayilan parametrelerle baslatilir."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream()
        self.assertEqual(ms.sample_rate, 48000)
        self.assertEqual(ms.block_size, 480)
        self.assertEqual(ms.channels, 1)
        self.assertIsNone(ms.on_audio)
        self.assertIsNone(ms._stream)
        self.assertIsNotNone(ms.suppressor)

    @patch("audio.microphone.NoiseSuppressor")
    def test_init_noise_suppression_disabled(self, mock_ns):
        """MicrophoneStream noise_suppression_enabled=False suppressor olusturmaz."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        self.assertIsNone(ms.suppressor)

    @patch("audio.microphone.NoiseSuppressor")
    def test_init_custom_params(self, mock_ns):
        """MicrophoneStream ozel parametrelerle baslatilir."""
        from audio.microphone import MicrophoneStream
        cb = lambda x: None
        ms = MicrophoneStream(
            sample_rate=16000,
            block_size=320,
            channels=2,
            noise_suppression_enabled=False,
            on_audio=cb,
        )
        self.assertEqual(ms.sample_rate, 16000)
        self.assertEqual(ms.block_size, 320)
        self.assertEqual(ms.channels, 2)
        self.assertIs(ms.on_audio, cb)
        self.assertIsNone(ms.suppressor)

    @patch("audio.microphone.NoiseSuppressor")
    @patch("sounddevice.InputStream")
    def test_start_creates_stream(self, mock_input_stream, mock_ns):
        """start() sounddevice.InputStream olusturur ve baslatir."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        mock_stream = MagicMock()
        mock_input_stream.return_value = mock_stream

        ms.start()

        mock_input_stream.assert_called_once()
        self.assertIsNotNone(ms._stream)
        mock_stream.start.assert_called_once()

    @patch("audio.microphone.NoiseSuppressor")
    @patch("sounddevice.InputStream")
    def test_start_idempotent(self, mock_input_stream, mock_ns):
        """start() ikinci kez cagrildiginda InputStream tekrar olusturulmaz."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        mock_stream = MagicMock()
        mock_input_stream.return_value = mock_stream

        ms.start()
        ms.start()

        mock_input_stream.assert_called_once()

    @patch("audio.microphone.NoiseSuppressor")
    @patch("sounddevice.InputStream")
    def test_stop_cleans_up_stream(self, mock_input_stream, mock_ns):
        """stop() stream'i durdurur ve kapatir."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        mock_stream = MagicMock()
        mock_input_stream.return_value = mock_stream

        ms.start()
        ms.stop()

        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
        self.assertIsNone(ms._stream)

    @patch("audio.microphone.NoiseSuppressor")
    @patch("sounddevice.InputStream")
    def test_stop_cleans_suppressor(self, mock_input_stream, mock_ns):
        """stop() suppressor._cleanup cagirir ve suppressor=None yapar."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=True)
        mock_suppressor = ms.suppressor
        mock_stream = MagicMock()
        mock_input_stream.return_value = mock_stream

        ms.start()
        ms.stop()

        mock_suppressor._cleanup.assert_called_once()
        self.assertIsNone(ms.suppressor)

    @patch("audio.microphone.NoiseSuppressor")
    def test_stop_no_stream(self, mock_ns):
        """stop() stream yokken hata firlatmaz."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        ms.stop()  # Should not raise

    @patch("audio.microphone.NoiseSuppressor")
    @patch("sounddevice.InputStream")
    def test_context_manager(self, mock_input_stream, mock_ns):
        """with statement start/stop cagirir."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        mock_stream = MagicMock()
        mock_input_stream.return_value = mock_stream

        with ms as mic:
            self.assertIs(mic, ms)
            self.assertIsNotNone(ms._stream)

        self.assertIsNone(ms._stream)

    @patch("audio.microphone.NoiseSuppressor")
    def test_audio_callback_mono(self, mock_ns):
        """_audio_callback mono veriyi on_audio'ya iletir."""
        from audio.microphone import MicrophoneStream
        captured = []
        ms = MicrophoneStream(noise_suppression_enabled=False, on_audio=lambda x: captured.append(x.copy()))
        indata = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)

        ms._audio_callback(indata, 3, None, None)

        self.assertEqual(len(captured), 1)
        np.testing.assert_array_almost_equal(captured[0], [0.1, 0.2, 0.3])

    @patch("audio.microphone.NoiseSuppressor")
    def test_audio_callback_stereo_to_mono(self, mock_ns):
        """_audio_callback stereo veriyi mono'ya indirger."""
        from audio.microphone import MicrophoneStream
        captured = []
        ms = MicrophoneStream(noise_suppression_enabled=False, on_audio=lambda x: captured.append(x.copy()))
        stereo = np.array([[0.1, 0.5], [0.2, 0.6], [0.3, 0.7]], dtype=np.float32)

        ms._audio_callback(stereo, 3, None, None)

        self.assertEqual(len(captured), 1)
        np.testing.assert_array_almost_equal(captured[0], [0.1, 0.2, 0.3])

    @patch("audio.microphone.NoiseSuppressor")
    def test_audio_callback_with_noise_suppression(self, mock_ns):
        """_audio_callback gurultu bastirma aktifken islenmis veriyi iletir."""
        from audio.microphone import MicrophoneStream
        captured = []
        ms = MicrophoneStream(noise_suppression_enabled=True, on_audio=lambda x: captured.append(x.copy()))
        ms.suppressor = MagicMock()
        ms.suppressor.enabled = True
        ms.suppressor.process_stream.return_value = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        indata = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)
        ms._audio_callback(indata, 3, None, None)

        ms.suppressor.process_stream.assert_called_once()
        np.testing.assert_array_almost_equal(captured[0], [0.0, 0.0, 0.0])

    @patch("audio.microphone.NoiseSuppressor")
    def test_audio_callback_no_on_audio(self, mock_ns):
        """_audio_callback on_audio yokken hata firlatmaz."""
        from audio.microphone import MicrophoneStream
        ms = MicrophoneStream(noise_suppression_enabled=False)
        indata = np.array([[0.1], [0.2]], dtype=np.float32)
        ms._audio_callback(indata, 2, None, None)  # Should not raise

    @patch("audio.microphone.NoiseSuppressor")
    def test_audio_callback_suppressor_error(self, mock_ns):
        """_audio_callback suppressor hata firlatirsa ham veriyi iletir."""
        from audio.microphone import MicrophoneStream
        captured = []
        ms = MicrophoneStream(noise_suppression_enabled=False, on_audio=lambda x: captured.append(x.copy()))
        ms.suppressor = MagicMock()
        ms.suppressor.enabled = True
        ms.suppressor.process_stream.side_effect = Exception("Test error")

        indata = np.array([[0.5], [0.6]], dtype=np.float32)
        ms._audio_callback(indata, 2, None, None)

        np.testing.assert_array_almost_equal(captured[0], [0.5, 0.6])


if __name__ == "__main__":
    unittest.main(verbosity=2)
