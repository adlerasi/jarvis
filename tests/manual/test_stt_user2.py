from core.audio_system.stt_engine import get_stt_engine
import numpy as np
import traceback

engine = get_stt_engine()
for e in engine._engines:
    if e.name == "faster-whisper":
        try:
            fake_audio = np.random.randint(-3000, 3000, size=16000*2, dtype=np.int16).tobytes()
            print("Direct transcribe faster-whisper...")
            e.transcribe(fake_audio, 16000)
        except Exception as ex:
            traceback.print_exc()
