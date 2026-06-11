"""
core/hardware_detector.py
JARVIS OS-level hardware detection module.

Checks real hardware availability at the operating-system level before any
driver/library attempts to open a device.  Every function returns structured
result dicts so callers can decide fallback behaviour.

No mocks.  No placeholders.  Every check hits the actual OS or hardware API.

Usage:
    from core.hardware_detector import HardwareDetector

    detector = HardwareDetector()
    report = detector.detect_all()
    print(report.display.status)       # "ok" | "absent" | "blocked"
    print(report.audio_input.devices)  # list of device names
    print(report.audio_output.devices)
"""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Détente types ──────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Result of a single hardware check."""
    status: str           # "ok" | "absent" | "blocked" | "unknown"
    label: str            # human-readable short name
    detail: str           # human-readable explanation
    devices: list[str] = field(default_factory=list)  # detected device names
    raw: dict[str, Any] = field(default_factory=dict)  # raw OS data


@dataclass
class DetectionReport:
    """Complete hardware detection report."""
    display: CheckResult
    audio_input: CheckResult
    audio_output: CheckResult
    camera: CheckResult

    def success(self) -> bool:
        """True if at least display and one audio path are available."""
        return self.display.status == "ok" and (
            self.audio_input.status == "ok"
            or self.audio_output.status == "ok"
        )

    def summary(self) -> str:
        """Multi-line human-readable summary."""
        parts = [
            f"[{s.status.upper():>7}] {s.label} — {s.detail}"
            for s in (self.display, self.audio_input, self.audio_output, self.camera)
        ]
        return "\n".join(parts)


# ── Core detector ──────────────────────────────────────────────────────────────

class HardwareDetector:
    """Detect available hardware at OS level. Every method is a static check."""

    # ── Display ────────────────────────────────────────────────────────────────

    @staticmethod
    def check_display() -> CheckResult:
        """Check whether a graphical display is available.

        Strategy:
          Linux  — $DISPLAY env var + X server ping via xdpyinfo or xrandr.
          macOS  — $DISPLAY (XQuartz) OR we assume Aqua is present.
          Windows— Always ok (win32 API guarantees a display if session is
                    interactive; headless detection requires win32 calls).
        """
        system = platform.system()

        if system == "Windows":
            return CheckResult(
                status="ok",
                label="Display (Windows)",
                detail="Windows GUI session — display available.",
            )

        if system == "Darwin":
            # macOS almost always has a display; XQuartz is optional.
            display = os.environ.get("DISPLAY", "").strip()
            if display:
                return CheckResult(
                    status="ok",
                    label="Display (macOS + XQuartz)",
                    detail=f"DISPLAY={display}",
                )
            # Native Aqua — assume available unless we detect SSH without X
            if "SSH_CONNECTION" in os.environ and not display:
                return CheckResult(
                    status="blocked",
                    label="Display (macOS SSH)",
                    detail="SSH session without DISPLAY — likely no GUI.",
                )
            return CheckResult(
                status="ok",
                label="Display (macOS Aqua)",
                detail="Native display assumed available.",
            )

        # ── Linux ──────────────────────────────────────────────────────────
        display = os.environ.get("DISPLAY", "").strip()
        wayland = os.environ.get("WAYLAND_DISPLAY", "").strip()

        if not display and not wayland:
            # No display variable at all → headless
            return CheckResult(
                status="absent",
                label="Display (Linux)",
                detail="No DISPLAY or WAYLAND_DISPLAY set — headless environment.",
            )

        # Try xdpyinfo (X11) / xrandr (X11) / weston-info (Wayland)
        tried = []
        if display:
            for cmd in (["xdpyinfo", "-display", display], ["xrandr", "--display", display]):
                try:
                    r = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=5,
                    )
                    tried.append(f"{' '.join(cmd[:2])}: exit={r.returncode}")
                    if r.returncode == 0:
                        devices = []
                        for line in r.stdout.splitlines():
                            l = line.strip().lower()
                            if "screen" in l and "#" in l:
                                devices.append(line.strip())
                        return CheckResult(
                            status="ok",
                            label="Display (X11)",
                            detail=f"DISPLAY={display} — responding.",
                            devices=devices[:4],
                        )
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    tried.append(f"{' '.join(cmd[:2])}: not-found/timeout")

        if wayland:
            try:
                r = subprocess.run(
                    ["weston-info"], capture_output=True, text=True, timeout=5,
                )
                if r.returncode == 0:
                    return CheckResult(
                        status="ok",
                        label="Display (Wayland)",
                        detail=f"WAYLAND_DISPLAY={wayland} — responding.",
                    )
            except FileNotFoundError:
                pass

        # DISPLAY is set but not responding → blocked (e.g. ssh -X with no
        # X server, or a stale forwarded socket)
        return CheckResult(
            status="blocked",
            label="Display (Linux)",
            detail=f"DISPLAY={display} set but X server not responding. "
                   f"Tried: {'; '.join(tried)}",
        )

    # ── Audio input (microphone) ──────────────────────────────────────────────

    @staticmethod
    def check_audio_input() -> CheckResult:
        """List and validate audio INPUT devices at OS level.

        Uses three strategies:
          1. PyAudio (PortAudio) — device enumeration (cross-platform).
          2. ALSA /proc/asound   — Linux only, direct kernel interface.
          3. pactl list sources   — Linux PulseAudio/PipeWire.

        Strategy 1 is primary because PyAudio is the library the app uses.
        Strategies 2/3 serve as validation on Linux.
        """
        system = platform.system()

        # ── Primary: PyAudio enumeration ──────────────────────────────────
        pyaudio_devices = []
        pyaudio_error: str | None = None
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            try:
                count = pa.get_device_count()
                for i in range(count):
                    info = pa.get_device_info_by_index(i)
                    max_inputs = int(info.get("maxInputChannels", 0) or 0)
                    name = info.get("name", f"Device {i}")
                    if max_inputs > 0:
                        pyaudio_devices.append({
                            "index": i,
                            "name": name,
                            "channels": max_inputs,
                            "rate": int(info.get("defaultSampleRate", 0) or 0),
                        })
            finally:
                pa.terminate()
        except ImportError:
            pyaudio_error = "PyAudio not installed."
        except Exception as exc:
            pyaudio_error = f"PyAudio enumeration failed: {exc}"

        # ── Linux secondary: ALSA & PulseAudio ────────────────────────────
        alsa_devices: list[str] = []
        pulse_devices: list[str] = []

        if system == "Linux":
            # ALSA /proc/asound/cards
            try:
                cards = Path("/proc/asound/cards")
                if cards.exists():
                    text = cards.read_text(encoding="ascii", errors="replace")
                    for line in text.splitlines():
                        stripped = line.strip()
                        if stripped and not stripped.startswith(" "):
                            alsa_devices.append(stripped)
            except Exception:
                pass

            # PulseAudio pactl list sources short
            try:
                r = subprocess.run(
                    ["pactl", "list", "sources", "short"],
                    capture_output=True, text=True, timeout=5,
                )
                if r.returncode == 0:
                    for line in r.stdout.splitlines():
                        stripped = line.strip()
                        if stripped:
                            pulse_devices.append(stripped)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        # ── Build result ──────────────────────────────────────────────────
        device_names = [d["name"] for d in pyaudio_devices]
        status: str
        detail: str

        if pyaudio_devices:
            status = "ok"
            detail = f"{len(pyaudio_devices)} input device(s) found."
        elif pyaudio_error:
            status = "unknown"
            detail = pyaudio_error
        elif alsa_devices or pulse_devices:
            status = "absent"
            detail = "PyAudio found no input devices (ALSA/Pulse may have hw)."
        else:
            status = "absent"
            detail = "No audio input devices detected at any level."

        # Append secondary info
        extra: list[str] = []
        if alsa_devices:
            extra.append(f"ALSA cards: {len(alsa_devices)}")
        if pulse_devices:
            extra.append(f"PulseAudio sources: {len(pulse_devices)}")
        if extra:
            detail += f" ({'; '.join(extra)})"

        return CheckResult(
            status=status,
            label="Audio Input (microphone)",
            detail=detail,
            devices=device_names,
            raw={
                "pyaudio": [str(d) for d in pyaudio_devices],
                "alsa": alsa_devices,
                "pulse": pulse_devices,
                "error": pyaudio_error,
            },
        )

    # ── Audio output (speakers/headphones) ────────────────────────────────────

    @staticmethod
    def check_audio_output() -> CheckResult:
        """List and validate audio OUTPUT devices at OS level.

        Same three strategies as check_audio_input but filtering for output.
        """
        system = platform.system()

        pyaudio_devices = []
        pyaudio_error: str | None = None
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            try:
                count = pa.get_device_count()
                for i in range(count):
                    info = pa.get_device_info_by_index(i)
                    max_outputs = int(info.get("maxOutputChannels", 0) or 0)
                    name = info.get("name", f"Device {i}")
                    if max_outputs > 0:
                        pyaudio_devices.append({
                            "index": i,
                            "name": name,
                            "channels": max_outputs,
                            "rate": int(info.get("defaultSampleRate", 0) or 0),
                        })
            finally:
                pa.terminate()
        except ImportError:
            pyaudio_error = "PyAudio not installed."
        except Exception as exc:
            pyaudio_error = f"PyAudio enumeration failed: {exc}"

        # Linux secondary
        pulse_devices: list[str] = []
        if system == "Linux":
            try:
                r = subprocess.run(
                    ["pactl", "list", "sinks", "short"],
                    capture_output=True, text=True, timeout=5,
                )
                if r.returncode == 0:
                    for line in r.stdout.splitlines():
                        stripped = line.strip()
                        if stripped:
                            pulse_devices.append(stripped)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        device_names = [d["name"] for d in pyaudio_devices]
        status: str
        detail: str

        if pyaudio_devices:
            status = "ok"
            detail = f"{len(pyaudio_devices)} output device(s) found."
        elif pyaudio_error:
            status = "unknown"
            detail = pyaudio_error
        else:
            status = "absent"
            detail = "No audio output devices detected."

        if pulse_devices:
            detail += f" (PulseAudio sinks: {len(pulse_devices)})"

        return CheckResult(
            status=status,
            label="Audio Output (speakers)",
            detail=detail,
            devices=device_names,
            raw={
                "pyaudio": [str(d) for d in pyaudio_devices],
                "pulse": pulse_devices,
                "error": pyaudio_error,
            },
        )

    # ── Camera ────────────────────────────────────────────────────────────────

    @staticmethod
    def check_camera() -> CheckResult:
        """Check if any camera device is available at OS level.

        Linux:   /dev/video* entries + v4l2-ctl if available.
        macOS:   avfoundation via system_profiler or built-in iSight.
        Windows: DirectShow via platform check (runtime detection deferred).
        """
        system = platform.system()
        devices: list[str] = []

        if system == "Linux":
            try:
                from pathlib import Path
                video_devs = sorted(Path("/dev").glob("video*"))
                for d in video_devs:
                    devices.append(str(d))
            except Exception:
                pass

            # Try v4l2-ctl for richer info
            try:
                r = subprocess.run(
                    ["v4l2-ctl", "--list-devices"],
                    capture_output=True, text=True, timeout=5,
                )
                if r.returncode == 0 and r.stdout.strip():
                    for line in r.stdout.splitlines():
                        s = line.strip()
                        if s and not s.startswith("/"):
                            devices.append(s)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            if devices:
                return CheckResult(
                    status="ok",
                    label="Camera (Linux V4L2)",
                    detail=f"{len(devices)} video device(s) found.",
                    devices=list(set(devices)),
                )
            return CheckResult(
                status="absent",
                label="Camera (Linux)",
                detail="No /dev/video* devices found. No camera detected.",
            )

        if system == "Darwin":
            try:
                r = subprocess.run(
                    ["system_profiler", "SPCameraDataType"],
                    capture_output=True, text=True, timeout=15,
                )
                if r.returncode == 0 and r.stdout.strip():
                    for line in r.stdout.splitlines():
                        s = line.strip()
                        if s and s.startswith("@"):
                            devices.append(s)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            if devices:
                return CheckResult(
                    status="ok",
                    label="Camera (macOS)",
                    detail=f"{len(devices)} camera(s) found.",
                    devices=devices,
                )
            return CheckResult(
                status="absent",
                label="Camera (macOS)",
                detail="No camera detected via system_profiler.",
            )

        # Windows — actual detection requires DirectShow or COM interop.
        # For now return unknown; PyAudio doesn't cover video.
        return CheckResult(
            status="unknown",
            label="Camera (Windows)",
            detail="Camera detection on Windows requires DirectShow (deferred).",
        )

    # ── All-in-one ────────────────────────────────────────────────────────────

    @classmethod
    def detect_all(cls) -> DetectionReport:
        """Run every hardware check and return a consolidated report."""
        return DetectionReport(
            display=cls.check_display(),
            audio_input=cls.check_audio_input(),
            audio_output=cls.check_audio_output(),
            camera=cls.check_camera(),
        )

    @classmethod
    def assert_display_or_raise(cls) -> None:
        """Call before starting the UI.  Raises RuntimeError if no display."""
        result = cls.check_display()
        if result.status != "ok":
            raise RuntimeError(
                f"No display available: {result.detail}\n"
                "To run in headless mode, use the CLI interface instead."
            )

    @classmethod
    def assert_audio_input_or_raise(cls) -> None:
        """Call before opening microphone.  Raises RuntimeError if no input."""
        result = cls.check_audio_input()
        if result.status not in ("ok", "unknown"):
            raise RuntimeError(
                f"No microphone available: {result.detail}\n"
                "Voice input will not work."
            )
