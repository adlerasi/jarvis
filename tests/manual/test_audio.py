import os
import sys
sys.path.insert(0, os.path.abspath("."))
from core.audio_system.tts_engine import get_tts_engine
tts = get_tts_engine()
print("TTS Engine:", tts._active_engine.name)
tts.speak("Merhaba, sistem test ediliyor.", blocking=True)
