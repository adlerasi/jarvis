import os
import sys
sys.path.insert(0, os.path.abspath("."))
from core.audio_system.tts_engine import PiperTTSEngine
p = PiperTTSEngine()
print("Model path:", p._model_path)
print("Config path:", p._config_path)
print("Is available:", p.is_available())
