from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import tempfile
import time
import webbrowser
from pathlib import Path


import traceback
IS_WINDOWS = os.name == "nt"

# Windows-specific imports
if IS_WINDOWS:
    import ctypes.wintypes  # type: ignore[import-untyped]
    import winreg
else:
    ctypes.wintypes = None  # type: ignore[unused-ignore]
    winreg = None


def open_url(url: str) -> None:
    webbrowser.open(url, new=2)


def copy_to_clipboard(text: str) -> tuple[bool, str]:
    try:
        if IS_WINDOWS:
            subprocess.run(["clip"], input=text, text=True, check=True, timeout=5)
        else:
            if shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True, timeout=5)
            elif shutil.which("xsel"):
                subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=True, timeout=5)
            else:
                pass
        return True, "ok"
    except Exception as exc:
        return False, f"Panoya kopyalanamadi: {exc}"


def _run_powershell(script: str, timeout: int = 20) -> subprocess.CompletedProcess:
    if not IS_WINDOWS:
        return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="PowerShell not supported on this platform")
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def open_windows_app(app_name: str) -> tuple[bool, str]:
    normalized = (app_name or "").strip()
    if not normalized:
        return False, "Uygulama adi belirtilmedi."

    if IS_WINDOWS:
        aliases = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "edge": "msedge",
            "microsoft edge": "msedge",
            "firefox": "firefox",
            "terminal": "wt",
            "windows terminal": "wt",
            "cmd": "cmd",
            "powershell": "powershell",
            "explorer": "explorer",
            "dosya gezgini": "explorer",
            "notepad": "notepad",
            "not defteri": "notepad",
            "calculator": "calc",
            "hesap makinesi": "calc",
            "spotify": "spotify",
            "whatsapp": "WhatsApp",
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",
        }
        target = aliases.get(normalized.lower(), normalized)
        try:
            if shutil.which(target):
                subprocess.Popen([target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"{normalized} acildi."
            escaped = target.replace("'", "''")
            result = _run_powershell(f"Start-Process '{escaped}'", timeout=10)
            if result.returncode == 0:
                return True, f"{normalized} acildi."
            detail = (result.stderr or result.stdout or "").strip()
            return False, detail or f"'{normalized}' bulunamadi veya acilamadi."
        except Exception as exc:
            return False, f"'{normalized}' acilamadi: {exc}"
    else:
        # Linux / Unix aliases
        aliases = {
            "chrome": "google-chrome",
            "google chrome": "google-chrome",
            "edge": "microsoft-edge",
            "microsoft edge": "microsoft-edge",
            "firefox": "firefox",
            "terminal": "gnome-terminal",
            "cmd": "gnome-terminal",
            "powershell": "gnome-terminal",
            "explorer": "xdg-open .",
            "dosya gezgini": "xdg-open .",
            "notepad": "gedit",
            "not defteri": "gedit",
            "calculator": "gnome-calculator",
            "hesap makinesi": "gnome-calculator",
            "spotify": "spotify",
            "whatsapp": "whatsapp-for-linux",
            "vscode": "code",
            "vs code": "code",
            "visual studio code": "code",
        }
        target = aliases.get(normalized.lower(), normalized)
        try:
            cmd = target.split() if " " in target else [target]
            if shutil.which(cmd[0]):
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"{normalized} acildi."
            subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"{normalized} acildi."
        except Exception as exc:
            return False, f"'{normalized}' acilamadi: {exc}"


def open_uri(uri: str) -> tuple[bool, str]:
    try:
        if IS_WINDOWS:
            os.startfile(uri)   # sadece Windows
        else:
            subprocess.Popen(["xdg-open", uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def press_enter_after_delay(delay: float) -> tuple[bool, str]:
    try:
        time.sleep(max(0.0, delay))
        import pyautogui  # pylint: disable=import-error

        pyautogui.press("enter")
        return True, "ok"
    except Exception as exc:
        return False, f"Otomatik tus basimi tamamlanamadi: {exc}"


def hotkey(*keys: str, delay: float = 0.0) -> tuple[bool, str]:
    try:
        if delay > 0:
            time.sleep(delay)
            import pyautogui  # pylint: disable=import-error

            pyautogui.hotkey(*keys)
        return True, "ok"
    except Exception as exc:
        return False, f"Klavye otomasyonu tamamlanamadi: {exc}"


def write_text(text: str, delay: float = 0.0) -> tuple[bool, str]:
    try:
        if delay > 0:
            time.sleep(delay)
            import pyautogui  # pylint: disable=import-error

            pyautogui.write(text)
        return True, "ok"
    except Exception as exc:
        return False, f"Yazi yazma otomasyonu tamamlanamadi: {exc}"


def speak_with_windows(text: str, voice: str = "") -> tuple[bool, str]:
    if not IS_WINDOWS:
        try:
            subprocess.run(["spd-say", "-w", "-l", "tr", text], check=True)
            return True, "ok"
        except Exception as exc:
            return False, str(exc)

    escaped_text = text.replace("'", "''")
    escaped_voice = voice.replace("'", "''")
    select_voice = (
        f"$v = $s.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Name -like '*{escaped_voice}*' }} | Select-Object -First 1; "
        "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; "
        if escaped_voice
        else ""
    )
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"{select_voice}"
        f"$s.Speak('{escaped_text}');"
    )
    try:
        result = _run_powershell(script, timeout=60)
        if result.returncode == 0:
            return True, "ok"
        return False, (result.stderr or result.stdout or "").strip()
    except Exception as exc:
        return False, str(exc)


def list_windows_voices() -> list[str]:
    if not IS_WINDOWS:
        return ["tr", "en"]

    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
    )
    try:
        result = _run_powershell(script, timeout=10)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def play_audio_file(path: Path, volume: float = 0.2) -> subprocess.Popen:
    if not IS_WINDOWS:
        vol_gain = int(max(0.0, min(1.0, float(volume))) * 100)
        return subprocess.Popen(
            ["mpg123", "-q", "-g", str(vol_gain), str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    safe_path = str(path).replace("'", "''")
    vol = max(0.0, min(1.0, float(volume)))
    script = (
        "Add-Type -AssemblyName PresentationCore; "
        "$p = New-Object System.Windows.Media.MediaPlayer; "
        f"$p.Open([Uri]::new('{safe_path}')); "
        f"$p.Volume = {vol}; "
        "$p.Play(); "
        "Start-Sleep -Milliseconds 300; "
        "while ($p.NaturalDuration.HasTimeSpan -and $p.Position -lt $p.NaturalDuration.TimeSpan) "
        "{ Start-Sleep -Milliseconds 120 }; "
        "$p.Close();"
    )
    return subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def get_active_window_title() -> tuple[str, str]:
    if not IS_WINDOWS:
        return "", ""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return "", buffer.value.strip()


def capture_active_window(output_path: Path | None = None) -> tuple[bool, str, dict]:
    try:
        from PIL import ImageGrab

        bbox = None
        owner_name, window_title = get_active_window_title()
        if IS_WINDOWS:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            rect = ctypes.wintypes.RECT()
            if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                if width > 0 and height > 0:
                    bbox = (rect.left, rect.top, rect.right, rect.bottom)
        image = ImageGrab.grab(bbox=bbox, all_screens=True)
        if output_path is None:
            handle = tempfile.NamedTemporaryFile(prefix="jarvis-screen-", suffix=".png", delete=False)
            output_path = Path(handle.name)
            handle.close()
        image.save(output_path)
        return True, "ok", {
            "image_path": str(output_path),
            "owner_name": owner_name,
            "window_title": window_title,
            "bounds": {},
            "detail": "windows_capture",
        }
    except Exception as exc:
        return False, str(exc), {}
