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


class TestNoiseSuppressor(unittest.TestCase):
    """NoiseSuppressor modül import ve bypass testleri."""

    def test_module_import(self):
        """audio.noise_suppressor import edilebilmeli."""
        from audio.noise_suppressor import NoiseSuppressor
        self.assertIsNotNone(NoiseSuppressor)

    def test_module_constants(self):
        """NoiseSuppressor sabitleri dogru olmali."""
        from audio.noise_suppressor import NoiseSuppressor
        self.assertEqual(NoiseSuppressor.SAMPLE_RATE, 48000)
        self.assertEqual(NoiseSuppressor.FRAME_SIZE, 480)
        self.assertIn(48000, NoiseSuppressor.SUPPORTED_RATES)
        self.assertIn(16000, NoiseSuppressor.SUPPORTED_RATES)

    def test_disabled_bypass(self):
        """enabled=False ile suppressor bypass modunda calismali."""
        from audio.noise_suppressor import NoiseSuppressor
        ns = NoiseSuppressor(sample_rate=48000, enabled=False)
        self.assertFalse(ns.enabled)
        # bypass'ta input aynen donmeli
        import numpy as np
        dummy = np.zeros(480, dtype=np.int16)
        result = ns.process_frame(dummy)
        np.testing.assert_array_equal(result, dummy)

    def test_unsupported_rate_bypass(self):
        """Desteklenmeyen sample rate'de bypass aktif olmali."""
        from audio.noise_suppressor import NoiseSuppressor
        ns = NoiseSuppressor(sample_rate=8000, enabled=True)
        self.assertFalse(ns.enabled)
        import numpy as np
        dummy = np.zeros(480, dtype=np.int16)
        result = ns.process_frame(dummy)
        np.testing.assert_array_equal(result, dummy)

    def test_process_16khz_no_rnnoise_bypass(self):
        """RNNoise kutuphanesi yokken process_16khz bypass etmeli."""
        from audio.noise_suppressor import NoiseSuppressor
        # enabled=True ama lib yok -> _load_library basarisiz -> enabled=False
        ns = NoiseSuppressor(sample_rate=16000, enabled=True)
        # Kutuphane olmadigi icin enabled=False olur
        import numpy as np
        dummy = np.zeros(480, dtype=np.int16)
        result = ns.process_16khz(dummy)
        np.testing.assert_array_equal(result, dummy)
        self.assertIsNotNone(result)

    def test_bypass_on_lib_missing(self):
        """Kutuphane yokken NoiseSuppressor hata firlatmamali, bypass'a dusmeli."""
        from audio.noise_suppressor import NoiseSuppressor
        ns = NoiseSuppressor(sample_rate=48000, enabled=True)
        # enabled=False olmali cunku lib yok (bu ortamda)
        if not ns.enabled:
            import numpy as np
            dummy = np.zeros(480, dtype=np.int16)
            result = ns.process_frame(dummy)
            np.testing.assert_array_equal(result, dummy)

    def test_vad_probability_default(self):
        """VAD probability baslangic degeri 0.0 olmali."""
        from audio.noise_suppressor import NoiseSuppressor
        ns = NoiseSuppressor(sample_rate=48000, enabled=False)
        self.assertEqual(ns.vad_probability, 0.0)

    def test_context_manager_bypass(self):
        """Context manager (with) bypass modunda calismali."""
        from audio.noise_suppressor import NoiseSuppressor
        with NoiseSuppressor(sample_rate=48000, enabled=False) as ns:
            self.assertFalse(ns.enabled)
            import numpy as np
            dummy = np.zeros(480, dtype=np.int16)
            result = ns.process_frame(dummy)
            np.testing.assert_array_equal(result, dummy)

    def test_audio_package_import(self):
        """audio paketinden NoiseSuppressor import edilebilmeli."""
        from audio import NoiseSuppressor
        self.assertIsNotNone(NoiseSuppressor)

    def test_audio_microphone_import(self):
        """audio.microphone import edilebilmeli (sounddevice opsiyonel)."""
        try:
            from audio.microphone import MicrophoneStream
            self.assertIsNotNone(MicrophoneStream)
        except ImportError:
            # sounddevice yoksa import basarisiz olabilir
            self.skipTest("sounddevice kurulu degil")


if __name__ == "__main__":
    unittest.main(verbosity=2)
