from core.audio_system.stt_engine import get_stt_engine
import numpy as np

engine = get_stt_engine()

# Generate 1.5 seconds of fake speech (white noise)
fake_audio = np.random.randint(-3000, 3000, size=16000*2, dtype=np.int16).tobytes()

print("Transcribing...")
text = engine.transcribe(fake_audio, sample_rate=16000)
print(f"Transcription result: '{text}'")
