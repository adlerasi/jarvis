import pyaudio
import numpy as np
import time
from core.audio_system.stt_engine import get_stt_engine
import scipy.signal

print("Initializing STT...")
engine = get_stt_engine()

p = pyaudio.PyAudio()
device_rate = 16000
target_rate = 16000

print("Opening PyAudio stream...")
stream = None
for rate in [16000, 48000, 44100]:
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=2048)
        device_rate = rate
        print(f"Successfully opened at {rate}Hz")
        break
    except Exception as e:
        print(f"Failed at {rate}Hz: {e}")

if not stream:
    print("Could not open microphone!")
    exit(1)

print("Listening for 5 seconds... PLEASE SPEAK!")
frames = []
for _ in range(int(device_rate / 2048 * 5)):
    data = stream.read(2048, exception_on_overflow=False)
    
    if device_rate != target_rate:
        pcm = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        samples = int(len(pcm) * target_rate / device_rate)
        resampled = scipy.signal.resample(pcm, samples)
        data = resampled.astype(np.int16).tobytes()
        
    frames.append(data)
    
    arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    rms = float(np.sqrt(np.mean(arr ** 2)))
    print(f"RMS: {rms:.2f}")

stream.close()
p.terminate()

audio_bytes = b"".join(frames)
print("Transcribing...")
text = engine.transcribe(audio_bytes, 16000)
print(f"\n--- TRANSCRIPTION RESULT ---\n'{text}'\n--------------------------")
