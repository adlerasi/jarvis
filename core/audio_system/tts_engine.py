"""
Cross-Platform TTS Engine
Piper (Linux) → pyttsx3 (Cross-platform) → edge-tts (Internet) → gTTS (Internet)
Auto-fallback chain.
"""

from __future__ import annotations

import platform
import subprocess
import tempfile
import threading
import wave
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np

from .audio_player import get_audio_player


class BaseTTSEngine(ABC):
    """Abstract TTS engine."""

    @abstractmethod
    def speak(self, text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
        """Speak text. Returns True on success."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name."""
        pass


class PiperTTSEngine(BaseTTSEngine):
    """Piper TTS - Local, fast, high quality (Linux preferred)."""

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or Path(__file__).parent.parent.parent / "voice" / "Fahrettin-TTS"
        self._model_path: Optional[Path] = None
        self._config_path: Optional[Path] = None
        self._detect_model()

    def _detect_model(self):
        """Auto-detect Piper model files."""
        if not self.model_dir.exists():
            return

        # Look for .onnx files
        onnx_files = list(self.model_dir.glob("*.onnx"))
        # Default paths
        self._model_path = Path("voice/Fahrettin-TTS/tr_TR-fahrettin-medium.onnx")
        self._config_path = Path("voice/Fahrettin-TTS/tr_TR-fahrettin-medium.onnx.json")
        if onnx_files:
            self._model_path = onnx_files[0]
            # Look for matching config
            config = self._model_path.with_suffix(".onnx.json")
            if config.exists():
                self._config_path = config

    @property
    def name(self) -> str:
        return "piper"

    def is_available(self) -> bool:
        if platform.system() == "Windows":
            return False  # Piper binary Windows'ta zor

        if self._model_path is None:
            return False

        # Check piper binary
        import os
        import shutil
        
        # Check standard PATH
        piper_path = shutil.which("piper")
        if piper_path:
            self._piper_bin = piper_path
            return True
            
        # Check ~/.local/bin/piper (for GUI/UI launches without proper PATH)
        import os
        import pwd
        
        # Determine actual user
        if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
            target_user = os.environ.get("SUDO_USER")
        else:
            target_user = pwd.getpwuid(os.getuid()).pw_name
            
        try:
            user_home = pwd.getpwnam(target_user).pw_dir
            local_piper = Path(user_home) / ".local" / "bin" / "piper"
            if local_piper.exists() and os.access(local_piper, os.X_OK):
                self._piper_bin = str(local_piper)
                return True
        except Exception:
            pass
                    
        return False

    def speak(self, text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
        if not self.is_available():
            return False

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav_path = f.name

            # Generate with Piper
            cmd = [
                getattr(self, "_piper_bin", "piper"),
                "--model", str(self._model_path),
                "--config", str(self._config_path),
                "--output_file", wav_path,
            ]
            
            import os
            if os.geteuid() == 0:
                sudo_user = os.environ.get("SUDO_USER")
                if sudo_user:
                    import pwd
                    uid = pwd.getpwnam(sudo_user).pw_uid
                    gid = pwd.getpwnam(sudo_user).pw_gid
                    os.chown(wav_path, uid, gid)
                    cmd = ["sudo", "-u", sudo_user] + cmd

            result = subprocess.run(
                cmd, input=text, text=True,
                capture_output=True, timeout=30
            )

            if result.returncode != 0 or not Path(wav_path).exists():
                return False

            # Play
            player = get_audio_player()
            success = player.play_wav(wav_path)

            # Cleanup
            Path(wav_path).unlink(missing_ok=True)
            return success

        except Exception as e:
            print(f"[PiperTTS] Error: {e}")
            return False


class Pyttsx3TTSEngine(BaseTTSEngine):
    """pyttsx3 TTS - Cross-platform, offline, system voices."""

    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "pyttsx3"

    def is_available(self) -> bool:
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def _get_engine(self):
        if self._engine is None:
            import pyttsx3
            try:
                self._engine = pyttsx3.init()
            except Exception:
                # Fallback drivers
                for driver in ["espeak", "nsss", "sapi5"]:
                    try:
                        self._engine = pyttsx3.init(driverName=driver)
                        break
                    except Exception:
                        continue

            if self._engine:
                self._engine.setProperty("rate", 150)
                self._engine.setProperty("volume", 0.9)
        return self._engine

    def speak(self, text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
        if not self.is_available():
            return False

        def _speak():
            try:
                with self._lock:
                    engine = self._get_engine()
                    if engine is None:
                        print("[Pyttsx3TTSEngine] Engine başlatılamadı")
                        return

                    # Set voice if specified
                    if voice:
                        voices = engine.getProperty("voices")
                        for v in voices:
                            if voice.lower() in v.name.lower():
                                engine.setProperty("voice", v.id)
                                break

                    engine.say(text)
                    engine.runAndWait()
            except Exception as e:
                print(f"[Pyttsx3TTSEngine] Speak error: {e}")

        if blocking:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

        return True


class EdgeTTSEngine(BaseTTSEngine):
    """edge-tts TTS - Internet required, Microsoft Neural voices."""

    def __init__(self):
        self._voice_map = {
            "tr-TR-AhmetNeural": "tr-TR-AhmetNeural",
            "tr-TR-EmelNeural": "tr-TR-EmelNeural",
            "ahmet": "tr-TR-AhmetNeural",
            "emel": "tr-TR-EmelNeural",
        }

    @property
    def name(self) -> str:
        return "edge-tts"

    def is_available(self) -> bool:
        try:
            import shutil
            return shutil.which("edge-tts") is not None
        except Exception:
            return False

    def speak(self, text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
        if not self.is_available():
            return False

        voice_id = self._voice_map.get(voice or "tr-TR-AhmetNeural", "tr-TR-AhmetNeural")

        def _speak():
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    mp3_path = f.name

                import subprocess
                result = subprocess.run(
                    ["edge-tts", "--voice", voice_id, "--text", text, "--write-media", mp3_path],
                    capture_output=True, timeout=30
                )

                if result.returncode != 0:
                    return

                # Convert MP3 to WAV or play directly
                player = get_audio_player()
                # Try to play MP3 directly if player supports it
                # Otherwise convert
                try:
                    import pydub
                    audio = pydub.AudioSegment.from_mp3(mp3_path)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        wav_path = f.name
                    audio.export(wav_path, format="wav")
                    player.play_wav(wav_path)
                    Path(wav_path).unlink(missing_ok=True)
                except ImportError:
                    # No pydub, try mpg123 directly
                    subprocess.run(["mpg123", "-q", mp3_path], timeout=60)

                Path(mp3_path).unlink(missing_ok=True)
            except Exception as e:
                print(f"[EdgeTTSEngine] Error: {e}")

        if blocking:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

        return True


class GTTSEngine(BaseTTSEngine):
    """gTTS TTS - Internet required, Google Translate TTS."""

    @property
    def name(self) -> str:
        return "gtts"

    def is_available(self) -> bool:
        try:
            from gtts import gTTS
            return True
        except ImportError:
            return False

    def speak(self, text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
        if not self.is_available():
            return False

        def _speak():
            try:
                from gtts import gTTS
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    mp3_path = f.name

                tts = gTTS(text=text, lang="tr", slow=False)
                tts.save(mp3_path)

                # Play
                try:
                    import pydub
                    audio = pydub.AudioSegment.from_mp3(mp3_path)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        wav_path = f.name
                    audio.export(wav_path, format="wav")

                    player = get_audio_player()
                    player.play_wav(wav_path)

                    Path(wav_path).unlink(missing_ok=True)
                except ImportError:
                    subprocess.run(["mpg123", "-q", mp3_path], timeout=60)

                Path(mp3_path).unlink(missing_ok=True)
            except Exception as e:
                print(f"[GTTSEngine] Error: {e}")

        if blocking:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

        return True


class TTSEngine:
    """Universal TTS - auto-selects best available engine with fallback."""

    _instance: Optional[TTSEngine] = None
    _lock = threading.Lock()

    # Fallback chain: Piper → pyttsx3 → edge-tts → gTTS
    _engine_chain = [
        PiperTTSEngine,
        Pyttsx3TTSEngine,
        EdgeTTSEngine,
        GTTSEngine,
    ]

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._engines: list[BaseTTSEngine] = []
        self._active_engine: Optional[BaseTTSEngine] = None
        self._detect_engines()

    def _detect_engines(self):
        """Detect all available TTS engines."""
        for engine_class in self._engine_chain:
            try:
                engine = engine_class()
                if engine.is_available():
                    self._engines.append(engine)
                    if self._active_engine is None:
                        self._active_engine = engine
                        print(f"[TTSEngine] Active: {engine.name}")
            except Exception as e:
                print(f"[TTSEngine] {engine_class.__name__} detection failed: {e}")

        if not self._engines:
            print("[TTSEngine] ⚠️ No TTS engine available!")

    def speak(self, text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
        """Speak with fallback chain."""
        if not text or not text.strip():
            return True

        # Try active engine first
        if self._active_engine:
            try:
                if self._active_engine.speak(text, voice, blocking):
                    return True
            except Exception as e:
                print(f"[TTSEngine] {self._active_engine.name} failed: {e}")

        # Fallback chain
        for engine in self._engines:
            if engine is self._active_engine:
                continue
            try:
                print(f"[TTSEngine] Fallback to {engine.name}")
                if engine.speak(text, voice, blocking):
                    self._active_engine = engine  # Promote to active
                    return True
            except Exception as e:
                print(f"[TTSEngine] {engine.name} failed: {e}")

        print("[TTSEngine] ❌ All TTS engines failed")
        return False

    def set_preferred_engine(self, engine_name: str) -> bool:
        """Manually set preferred engine."""
        for engine in self._engines:
            if engine.name == engine_name.lower():
                self._active_engine = engine
                print(f"[TTSEngine] Preferred: {engine_name}")
                return True
        print(f"[TTSEngine] Engine not available: {engine_name}")
        return False

    def list_engines(self) -> list[str]:
        """List available engine names."""
        return [e.name for e in self._engines]

    def get_active_engine(self) -> Optional[str]:
        if self._active_engine:
            return self._active_engine.name
        return None


# Global instance
_tts_engine: Optional[TTSEngine] = None

def get_tts_engine() -> TTSEngine:
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine


def speak_text(text: str, voice: Optional[str] = None, blocking: bool = False) -> bool:
    """Universal speak function."""
    return get_tts_engine().speak(text, voice, blocking)
