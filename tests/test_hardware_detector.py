#!/usr/bin/env python3
"""
JARVIS — Hardware Detector Integration Tests

Every test calls the real OS-level hardware detection APIs:
  - Display detection via $DISPLAY, xdpyinfo, /proc/asound
  - Audio input detection via PyAudio device enumeration
  - Audio output detection via PyAudio device enumeration
  - Camera detection via /dev/video* and v4l2-ctl

No mocks.  No patches.  No fake hardware.
If the test environment lacks certain hardware the test reports 'skipped'
with a clear reason, so CI does not fail on a headless build server.
"""

from __future__ import annotations

import os as _os
import sys
import unittest
from pathlib import Path

# Add project root to path
_BASE = Path(__file__).resolve().parent.parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))


# =============================================================================
# Hardware Detection Tests
# =============================================================================

class TestHardwareDetectorModule(unittest.TestCase):
    """Module imports and data structures."""

    def test_module_import(self):
        """hardware_detector module import edilebilmeli."""
        from core import hardware_detector
        self.assertIsNotNone(hardware_detector)
        self.assertTrue(hasattr(hardware_detector, "HardwareDetector"))
        self.assertTrue(hasattr(hardware_detector, "CheckResult"))
        self.assertTrue(hasattr(hardware_detector, "DetectionReport"))

    def test_check_result_dataclass(self):
        """CheckResult alanlari dogru sekilde olusturulabiliyor."""
        from core.hardware_detector import CheckResult
        r = CheckResult(status="ok", label="Test", detail="test detail")
        self.assertEqual(r.status, "ok")
        self.assertEqual(r.label, "Test")
        self.assertEqual(r.detail, "test detail")
        self.assertEqual(r.devices, [])
        self.assertEqual(r.raw, {})

    def test_detection_report_dataclass(self):
        """DetectionReport dumy CheckResult'larla olusturulabiliyor."""
        from core.hardware_detector import CheckResult, DetectionReport
        ok = lambda: CheckResult(status="ok", label="x", detail="x")
        r = DetectionReport(display=ok(), audio_input=ok(), audio_output=ok(), camera=ok())
        self.assertTrue(r.success())
        self.assertIsInstance(r.summary(), str)
        self.assertIn("OK", r.summary())

    def test_detection_report_failure(self):
        """DetectionReport display yoksa success False donmeli."""
        from core.hardware_detector import CheckResult, DetectionReport
        ok = lambda: CheckResult(status="ok", label="x", detail="x")
        fail = lambda: CheckResult(status="absent", label="x", detail="x")
        r = DetectionReport(display=fail(), audio_input=fail(), audio_output=ok(), camera=ok())
        self.assertFalse(r.success())


# =============================================================================
# Display Detection (real OS check)
# =============================================================================

class TestDisplayDetection(unittest.TestCase):
    """Real display detection — no mocks."""

    def test_check_display_returns_result(self):
        """check_display() her zaman bir CheckResult dondurmeli."""
        from core.hardware_detector import HardwareDetector, CheckResult
        result = HardwareDetector.check_display()
        self.assertIsInstance(result, CheckResult)
        self.assertIn(result.status, ("ok", "absent", "blocked", "unknown"))
        self.assertTrue(result.label)
        self.assertTrue(result.detail)

    def test_display_status_ok_if_env_set(self):
        """DISPLAY ortam degiskeni varsa status 'ok' veya 'blocked' olmali."""
        # Bu gerçek bir OS seviyesi testidir — eğer DISPLAY yoksa absent döner.
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_display()
        display = _os.environ.get("DISPLAY", "")
        wayland = _os.environ.get("WAYLAND_DISPLAY", "")
        if display or wayland:
            # DISPLAY set edilmis ama X server yanit vermiyor olabilir (ssh -X)
            self.assertIn(result.status, ("ok", "blocked"),
                          f"DISPLAY={display}, WAYLAND={wayland} → {result.status}")
        else:
            # Headless ortam
            self.assertEqual(result.status, "absent",
                             f"No DISPLAY env, expected absent, got {result.status}")


# =============================================================================
# Audio Input Detection (real PyAudio)
# =============================================================================

class TestAudioInputDetection(unittest.TestCase):
    """Real microphone detection via PyAudio — no mocks."""

    def test_check_audio_input_returns_result(self):
        """check_audio_input() her zaman bir CheckResult dondurmeli."""
        from core.hardware_detector import HardwareDetector, CheckResult
        result = HardwareDetector.check_audio_input()
        self.assertIsInstance(result, CheckResult)
        self.assertIn(result.status, ("ok", "absent", "unknown"))
        self.assertTrue(result.label)
        self.assertTrue(result.detail)
        # devices bir liste olmali
        self.assertIsInstance(result.devices, list)

    def test_audio_input_devices_are_strings(self):
        """Cihaz isimleri string olmali."""
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_audio_input()
        for d in result.devices:
            self.assertIsInstance(d, str)
            self.assertTrue(len(d) > 0)

    def test_input_devices_count_matches_pyaudio(self):
        """HardwareDetector'un buldugu cihaz sayisi PyAudio ile eslesmeli."""
        try:
            import pyaudio
        except ImportError:
            self.skipTest("PyAudio not installed")
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_audio_input()

        # PyAudio ile karsilastirma
        pa = pyaudio.PyAudio()
        try:
            pa_count = 0
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    pa_count += 1
        finally:
            pa.terminate()

        self.assertEqual(len(result.devices), pa_count,
                         f"HardwareDetector: {len(result.devices)}, PyAudio: {pa_count}")


# =============================================================================
# Audio Output Detection (real PyAudio)
# =============================================================================

class TestAudioOutputDetection(unittest.TestCase):
    """Real speaker/headphone detection via PyAudio — no mocks."""

    def test_check_audio_output_returns_result(self):
        """check_audio_output() her zaman bir CheckResult dondurmeli."""
        from core.hardware_detector import HardwareDetector, CheckResult
        result = HardwareDetector.check_audio_output()
        self.assertIsInstance(result, CheckResult)
        self.assertIn(result.status, ("ok", "absent", "unknown"))
        self.assertTrue(result.label)
        self.assertTrue(result.detail)
        self.assertIsInstance(result.devices, list)

    def test_audio_output_devices_are_strings(self):
        """Cihaz isimleri string olmali."""
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_audio_output()
        for d in result.devices:
            self.assertIsInstance(d, str)
            self.assertTrue(len(d) > 0)

    def test_output_devices_count_matches_pyaudio(self):
        """HardwareDetector'un buldugu cikis cihazi sayisi PyAudio ile eslesmeli."""
        try:
            import pyaudio
        except ImportError:
            self.skipTest("PyAudio not installed")
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_audio_output()

        pa = pyaudio.PyAudio()
        try:
            pa_count = 0
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxOutputChannels", 0) > 0:
                    pa_count += 1
        finally:
            pa.terminate()

        self.assertEqual(len(result.devices), pa_count,
                         f"HardwareDetector: {len(result.devices)}, PyAudio: {pa_count}")


# =============================================================================
# Camera Detection (real OS)
# =============================================================================

class TestCameraDetection(unittest.TestCase):
    """Real camera detection via /dev/video* and v4l2-ctl — no mocks."""

    def test_check_camera_returns_result(self):
        """check_camera() her zaman bir CheckResult dondurmeli."""
        from core.hardware_detector import HardwareDetector, CheckResult
        result = HardwareDetector.check_camera()
        self.assertIsInstance(result, CheckResult)
        self.assertIn(result.status, ("ok", "absent", "unknown"))
        self.assertTrue(result.label)
        self.assertTrue(result.detail)
        self.assertIsInstance(result.devices, list)

    def test_camera_devices_consistent_with_dev_video(self):
        """Linux'ta kamera cihazlari /dev/video* ile tutarli olmali."""
        import platform
        if platform.system() != "Linux":
            self.skipTest("Camera check is Linux-specific for /dev/video*")

        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_camera()

        # Gerçek /dev/video* dosyalari
        video_devs = sorted(Path("/dev").glob("video*"))
        video_names = [str(d) for d in video_devs]

        if video_names:
            self.assertEqual(result.status, "ok",
                             f"/dev/video* var ({video_names}) ama detector {result.status} dedi.")
            for v in video_names:
                self.assertIn(v, result.devices)
        else:
            self.assertEqual(result.status, "absent",
                             f"/dev/video* yok, detector {result.status} donmeli.")


# =============================================================================
# Detection Report (all checks combined)
# =============================================================================

class TestDetectionReport(unittest.TestCase):
    """Birlesik DetectionReport testi."""

    def test_detect_all_returns_report(self):
        """detect_all() butun donanimlari kontrol edip rapor donmeli."""
        from core.hardware_detector import HardwareDetector, DetectionReport
        report = HardwareDetector.detect_all()
        self.assertIsInstance(report, DetectionReport)

        # Her alan bir CheckResult olmali
        for field in ("display", "audio_input", "audio_output", "camera"):
            result = getattr(report, field)
            self.assertIsNotNone(result, f"{field} is None")
            from core.hardware_detector import CheckResult
            self.assertIsInstance(result, CheckResult, f"{field} is not CheckResult")
            self.assertIn(result.status, ("ok", "absent", "blocked", "unknown"))

    def test_detect_all_runs_without_error(self):
        """detect_all() hic hata firlatmamali."""
        from core.hardware_detector import HardwareDetector
        try:
            report = HardwareDetector.detect_all()
            self.assertIsNotNone(report)
        except Exception as e:
            self.fail(f"detect_all() raised {type(e).__name__}: {e}")

    def test_summary_includes_all_sections(self):
        """summary() tum donanim kategorilerini icermeli."""
        from core.hardware_detector import HardwareDetector
        report = HardwareDetector.detect_all()
        summary = report.summary()
        for keyword in ("Display", "Audio Input", "Audio Output", "Camera"):
            self.assertIn(keyword, summary,
                          f"'{keyword}' not found in summary:\n{summary}")


# =============================================================================
# Guard methods
# =============================================================================

class TestGuardMethods(unittest.TestCase):
    """assert_display_or_raise ve assert_audio_input_or_raise testleri."""

    def test_assert_display_or_raise_passes_with_display(self):
        """Ekran varsa assert_display_or_raise hata firlatmamali."""
        from core.hardware_detector import HardwareDetector
        import os
        if not os.environ.get("DISPLAY", "") and not os.environ.get("WAYLAND_DISPLAY", ""):
            self.skipTest("No display in this environment")
        try:
            HardwareDetector.assert_display_or_raise()
        except RuntimeError as e:
            self.fail(f"assert_display_or_raise() raised RuntimeError when display exists: {e}")

    def test_assert_display_or_raise_raises_without_display(self):
        """Ekran yoksa assert_display_or_raise RuntimeError firlatmali."""
        from core.hardware_detector import HardwareDetector
        import os
        if os.environ.get("DISPLAY", "") or os.environ.get("WAYLAND_DISPLAY", ""):
            self.skipTest("Display exists in this environment")
        with self.assertRaises(RuntimeError):
            HardwareDetector.assert_display_or_raise()


# =============================================================================
# Cross-platform raw data
# =============================================================================

class TestRawData(unittest.TestCase):
    """Raw data alanlarinin tutarliligi."""

    def test_audio_input_raw_contains_pyaudio_key(self):
        """Audio input raw dict 'pyaudio' anahtarini icermeli."""
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_audio_input()
        self.assertIn("pyaudio", result.raw)

    def test_audio_output_raw_contains_pyaudio_key(self):
        """Audio output raw dict 'pyaudio' anahtarini icermeli."""
        from core.hardware_detector import HardwareDetector
        result = HardwareDetector.check_audio_output()
        self.assertIn("pyaudio", result.raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
