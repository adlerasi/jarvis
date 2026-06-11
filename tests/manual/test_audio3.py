import os
import sys
import tempfile
sys.path.insert(0, os.path.abspath("."))
from core.audio_system.tts_engine import get_tts_engine
tts = get_tts_engine()
print("TTS Engine:", tts._active_engine.name)
tts.speak("Ses deneme bir ki üç. Sistem tamamen çalışıyor.", blocking=True)
