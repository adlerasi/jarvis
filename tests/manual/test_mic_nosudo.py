import pyaudio
import numpy as np

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True, frames_per_buffer=2048)

print("Dinleniyor (Sudo YOk)...")
for _ in range(10):
    data = stream.read(2048, exception_on_overflow=False)
    arr = np.frombuffer(data, dtype=np.int16)
    rms = np.sqrt(np.mean(arr.astype(np.float32)**2))
    print(f"RMS: {rms:.2f}")

stream.stop_stream()
stream.close()
p.terminate()
