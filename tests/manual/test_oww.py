import numpy as np
import pyaudio
import scipy.signal
from openwakeword import Model

oww = Model()
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True, frames_per_buffer=2048)

print("Lütfen 'Hey Jarvis' deyin...")
for _ in range(150):
    data = stream.read(2048, exception_on_overflow=False)
    pcm = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    resampled = scipy.signal.resample(pcm, int(len(pcm) * 16000 / 48000))
    audio_int16 = resampled.astype(np.int16)
    
    scores = oww.predict(audio_int16)
    for kw, score in scores.items():
        if score > 0.5:
            print(f"BINGO! {kw} -> {score}")

stream.stop_stream()
stream.close()
p.terminate()
