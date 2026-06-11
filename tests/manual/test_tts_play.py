import subprocess
import os

from core.audio_system.tts_engine import get_tts_engine

tts = get_tts_engine()
print("TTS Engine:", type(tts).__name__)
success = tts.speak("Bu bir ses testidir. Jarvis konuşuyor.")
print("TTS Success:", success)

