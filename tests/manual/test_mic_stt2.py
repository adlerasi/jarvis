import pyaudio
import numpy as np
import scipy.signal
from faster_whisper import WhisperModel

print("Loading Whisper...")
model = WhisperModel("base", device="cpu", compute_type="int8")

p = pyaudio.PyAudio()
device_rate = 16000

stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2048)

print("Listening for 5 seconds... SAY SOMETHING!")
frames = []
for _ in range(int(16000 / 2048 * 5)):
    data = stream.read(2048, exception_on_overflow=False)
    frames.append(data)

stream.close()
p.terminate()

audio_data = b"".join(frames)
audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

print("Transcribing with VAD=True...")
segments_vad, _ = model.transcribe(audio_array, beam_size=5, language="tr", vad_filter=True)
text_vad = " ".join([s.text for s in segments_vad])
print(f"VAD=True result: '{text_vad}'")

print("Transcribing with VAD=False...")
segments_novad, _ = model.transcribe(audio_array, beam_size=5, language="tr", vad_filter=False)
text_novad = " ".join([s.text for s in segments_novad])
print(f"VAD=False result: '{text_novad}'")
