"""
Emotional TTS — modifies speech parameters based on emotion.
Maps emotions to voice modifiers (speed, pitch, volume).
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import traceback

__all__ = ["EmotionTTS"]

BASE_DIR = Path(__file__).resolve().parent.parent

# Emotion → (speed_multiplier, pitch_modifier, volume_modifier)
_EMOTION_PROFILES: dict[str, tuple[float, int, float]] = {
    "neutral": (1.0, 0, 1.0),
    "happy":   (1.15, 2, 1.0),
    "sad":     (0.85, -2, 0.8),
    "angry":   (1.2, 3, 1.2),
    "excited": (1.25, 3, 1.1),
    "calm":    (0.9, -1, 0.9),
    "whisper": (0.7, -3, 0.4),
}

_EMOTION_KEYWORDS: dict[str, list[str]] = {
    "happy":   ["harika", "muthis", "super", "cok guzel", "sevindim", "😊", "🎉"],
    "sad":     ["uzgunum", "malesef", "kotu haber", "ne yazik ki", "😔", "😢"],
    "angry":   ["keske", "sinir", "cok kizgin", "dikkat et", "😠"],
    "excited": ["vay", "harika haber", "beklemedik", "oha", "🔥", "⭐"],
    "calm":    ["sakin", "rahat", "huzurlu", "dinlen", "🧘"],
}


def _detect_emotion(text: str) -> str:
    """Heuristic emotion detection from text."""
    lower = text.lower()
    for emotion, keywords in _EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return emotion
    # Exclamation heuristic
    if text.count("!") >= 2:
        return "excited"
    if text.count("?") >= 2:
        return "calm"
    return "neutral"


def _generate_piper_flags(speed: float) -> list[str]:
    """Generate Piper CLI flags for speed."""
    flags = []
    if speed != 1.0:
        flags.extend(["--speed", str(round(speed, 2))])
    return flags


def _generate_edge_ssml(text: str, speed: float, pitch: int) -> str:
    """Wrap text in SSML with prosody tags for edge-tts."""
    rate = f"{int((speed - 1.0) * 100):+d}%"
    pitch_str = f"{pitch:+d}st" if pitch else "0st"
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="tr-TR">'
        f'<prosody rate="{rate}" pitch="{pitch_str}">'
        f"{text}</prosody></speak>"
    )


def _generate_spd_say_flags(speed: float, pitch: int) -> list[str]:
    """Generate spd-say flags for rate and pitch."""
    flags = []
    # spd-say rate: -50 (slow) to +100 (fast), default 0
    rate = int((speed - 1.0) * 50)
    if rate != 0:
        flags.extend(["-r", str(rate)])
    # spd-say pitch: -100 (low) to +100 (high), default 0
    if pitch:
        flags.extend(["-p", str(pitch * 10)])
    return flags


class EmotionTTS:
    """
    Emotional TTS engine.

    Wraps existing TTS backends with emotion-based parameter modification.
    Supports: piper, edge-tts, spd-say (same chain as actions.tts).
    """

    def __init__(self, default_voice: str = "piper-fahrettin", default_emotion: str = "neutral"):
        self.voice = default_voice
        self._emotion = default_emotion

    # ── Emotion ───────────────────────────────────────────────────────────────

    def set_emotion(self, emotion: str):
        emotion = emotion.lower().strip()
        if emotion in _EMOTION_PROFILES:
            self._emotion = emotion
        else:
            print(f"[EmotionTTS] Bilinmeyen duygu: {emotion}, neutral kullaniliyor")
            self._emotion = "neutral"

    def get_emotion(self) -> str:
        return self._emotion

    def set_voice(self, voice_id: str):
        self.voice = voice_id

    # ── Speaking ──────────────────────────────────────────────────────────────

    def speak(self, text: str, emotion: Optional[str] = None, blocking: bool = False):
        """Speak with emotion-modified voice."""
        emotion = emotion or self._emotion
        if emotion not in _EMOTION_PROFILES:
            emotion = "neutral"
        speed, pitch, volume = _EMOTION_PROFILES[emotion]

        try:
            if self.voice == "piper-fahrettin":
                self._speak_piper_emotion(text, speed)
            elif self.voice.startswith("edge-"):
                self._speak_edge_emotion(text, speed, pitch, self.voice)
            else:
                self._speak_spd_emotion(text, speed, pitch)
        except Exception as exc:
            print(f"[EmotionTTS] Konusma hatasi: {exc}")
            traceback.print_exc()

    def _speak_piper_emotion(self, text: str, speed: float):
        """Piper TTS with speed modification."""
        try:
            _PIPER_FAHRETTIN_ONNX = BASE_DIR / "voice" / "Fahrettin-TTS" / "tr_TR-fahrettin-medium.onnx"
            _PIPER_FAHRETTIN_CFG = BASE_DIR / "voice" / "Fahrettin-TTS" / "tr_TR-fahrettin-medium.onnx.json"

            import shutil
            piper_bin = shutil.which("piper")
            if not piper_bin or not _PIPER_FAHRETTIN_ONNX.exists():
                return

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name

            cmd = [
                piper_bin,
                "--model", str(_PIPER_FAHRETTIN_ONNX),
                "--config", str(_PIPER_FAHRETTIN_CFG),
                "--output_file", wav_path,
            ]
            cmd.extend(_generate_piper_flags(speed))

            result = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=30)
            if result.returncode == 0 and Path(wav_path).exists():
                import sounddevice as sd
                from scipy.io import wavfile
                sr, data = wavfile.read(wav_path)
                sd.play(data, sr)
                sd.wait()
        except Exception:
            traceback.print_exc()
        finally:
            try:
                if wav_path and Path(wav_path).exists():
                    Path(wav_path).unlink()
            except Exception:
                traceback.print_exc()

    def _speak_edge_emotion(self, text: str, speed: float, pitch: int, voice_id: str):
        """Edge TTS with SSML prosody."""
        try:
            ssml = _generate_edge_ssml(text, speed, pitch)

            import shutil
            edge_bin = shutil.which("edge-tts")
            if not edge_bin:
                return

            voice_name = {
                "edge-ahmet": "tr-TR-AhmetNeural",
                "edge-emel": "tr-TR-EmelNeural",
            }.get(voice_id, "tr-TR-AhmetNeural")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3_path = f.name

            result = subprocess.run(
                [edge_bin, "--voice", voice_name, "--text", ssml, "--write-media", mp3_path],
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and Path(mp3_path).exists():
                subprocess.run(["mpg123", "-q", mp3_path], timeout=60)
        except Exception:
            traceback.print_exc()
        finally:
            try:
                if mp3_path and Path(mp3_path).exists():
                    Path(mp3_path).unlink()
            except Exception:
                traceback.print_exc()

    def _speak_spd_emotion(self, text: str, speed: float, pitch: int):
        """spd-say with rate/pitch modification."""
        try:
            cmd = ["spd-say", "-w", "-l", "tr"]
            cmd.extend(_generate_spd_say_flags(speed, pitch))
            cmd.append(text)
            subprocess.run(cmd, timeout=60)
        except Exception:
            traceback.print_exc()

    def speak_with_emphasis(
        self,
        text: str,
        important_parts: list[str],
        emotion: Optional[str] = None,
        blocking: bool = False,
    ):
        """
        Speak with emphasis on key phrases.

        Adds extra pauses before important parts.
        """
        modified = text
        for part in important_parts:
            if part in modified:
                modified = modified.replace(part, f"... {part} ...")
        self.speak(modified, emotion=emotion, blocking=blocking)
