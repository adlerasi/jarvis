import pyaudio
import numpy as np
import time

p = pyaudio.PyAudio()
try:
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2048)
    print("Stream opened successfully.")
    for _ in range(5):
        data = stream.read(2048, exception_on_overflow=False)
        rms = np.sqrt(np.mean(np.frombuffer(data, dtype=np.int16).astype(np.float32)**2))
        print(f"RMS: {rms:.2f}")
        time.sleep(0.1)
    stream.close()
except Exception as e:
    print(f"Error: {e}")
finally:
    p.terminate()
