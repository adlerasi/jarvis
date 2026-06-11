# STT (Speech-to-Text) & TTS (Text-to-Speech)

## STT Sistemi

JARVIS, backend tipine göre 2 farklı STT sistemi kullanır:

```
Gemini modu:     Gemini Live Audio API (bulut, streaming)
Ollama modu:     Google STT (birincil) → faster-whisper (fallback)
```

### Gemini STT (Live API)

- **Kullanılan kütüphane/model:** `google.genai` + Gemini Audio API
- **Ses kaynağı seçimi:** PyAudio stream (16kHz, paInt16, mono)
- **Noise cancellation:** RNNoise (ön işleme, opsiyonel)
- **Streaming vs Batch:** Gerçek zamanlı bidirectional streaming
- **Dil desteği:** Otomatik algılama (Gemini)
- **Gecikme:** ~300-500ms (uçtan uca)

```
Mikrofon → PyAudio (16kHz) → Gemini Live API
         ← Gemini Live API → Transkripsiyon + Tool calls
```

### Ollama STT (Local)

- **Kullanılan kütüphane/model:** `SpeechRecognition` (Google STT) → `faster-whisper`
- **Ses kaynağı seçimi:** PyAudio stream (16kHz, paInt16, mono)
- **Noise cancellation:** RNNoise (opsiyonel) + VAD
- **Streaming vs Batch:** Batch (konuşma bitince transkript)
- **Dil desteği:** Türkçe (faster-whisper language="tr")
- **Gecikme:** ~500ms-2sn

```
Mikrofon → RNNoise → VAD (FahrettinVAD) → f-w transcribe → text_utils clean
         ↑                                                   ↓
         └────────── PyAudio callback loop ─────────────────┘
```

### Streaming STT (`core/streaming_stt.py`)

```python
class StreamingSTT:
    """
    Gerçek zamanlı STT motoru.
    - Queue-based async transcription
    - VAD filtering
    - Turkish syllable-split correction
    - Partial/final transcription callbacks
    """
    
    def __init__(self, model_path=None, device="cpu", 
                 language="tr", beam_size=1, ...):
        self.model = WhisperModel(model_path or "base", 
                                   device=device, 
                                   compute_type="int8")
        self.vad_filter = True
        self.on_transcription = None  # callback
        self.on_partial = None        # partial callback
    
    def transcribe_chunk(self, audio_bytes: bytes) -> str:
        segments, _ = self.model.transcribe(
            audio_bytes, 
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
        )
        text = " ".join(seg.text for seg in segments)
        return fix_turkish_syllable_split(text)
```

### Ses Kaynağı Seçimi

```python
# core/gemini_provider.py — Audio device enumeration
from core.hardware_detector import HardwareDetector

audio = HardwareDetector.check_audio()
if audio.status != "ok":
    raise RuntimeError(f"Mikrofon bulunamadi: {audio.detail}")

# PyAudio stream aç
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    input_device_index=audio.device_index,
    frames_per_buffer=1024,
)
```

### Metin Temizleme (`core/text_utils.py`)

```python
def clean_transcript_text(text: str) -> str:
    # 1. NFC normalize
    text = unicodedata.normalize("NFC", text)
    # 2. Hece bölmesi birleştirme (faster-whisper Türkçe bug)
    text = fix_turkish_syllable_split(text)
    return text.strip()
```

## TTS Sistemi

JARVIS'te **2 TTS zinciri** bulunur:

```
Gemini modu:     Gemini Live Audio API (doğal ses, streaming)
Ollama modu:     Piper → edge-tts → spd-say (fallback zinciri)
```

### Gemini TTS (Live API)

- **Kullanılan kütüphane/model:** Gemini Audio API (doğal konuşma)
- **Ses çıkış cihazı yönetimi:** PyAudio (24kHz, paInt16, mono)
- **Queue / Interruption handling:** `audio_in_queue` (asyncio.Queue)
- **Ses hızı / ton ayarı:** Ses modeli seçimiyle (voice: Charon, Puck, Aoede, Kore...)
- **Streaming:** Evet, token token ses akışı

```
Gemini API response → audio_in_queue → PyAudio playback (24kHz)
                          ↑
                    Barge-In kesintisi → queue.clear()
```

### Ollama TTS (Local)

- **Kullanılan kütüphane/model:** Piper (offline) → edge-tts (bulut) → spd-say (sistem)
- **Ses çıkış cihazı yönetimi:** subprocess (aplay/mpg123)
- **Queue / Interruption handling:** Thread lock + cancel mekanizması
- **Ses hızı / ton ayarı:** Sadece edge-tts (prosody SSML)

```python
# actions/tts.py — TTS zinciri
class TTSEngine:
    def speak(self, text: str):
        # 1. Piper (yerel, offline)
        if self._piper_available:
            return self._speak_piper(text)
        # 2. Edge-TTS (bulut)
        if self._edge_available:
            return self._speak_edge(text)
        # 3. spd-say (sistem sesi)
        return self._speak_spdsay(text)
    
    def _speak_piper(self, text: str):
        # echo "..." | piper --model tr_TR-fahrettin-medium.onnx --output-raw | aplay
        cmd = f'echo "{text}" | piper ... | aplay'
        subprocess.run(cmd, shell=True, timeout=30)
```

### Streaming TTS (`core/streaming_tts.py`)

```python
class StreamingTTS:
    """
    Cümle cümle TTS çalma.
    - Metni cümlelere böler
    - Her cümleyi sırayla TTS'e gönderir
    - Barge-In ile kesilebilir
    """
    
    def __init__(self, on_sentence_start=None, on_sentence_end=None):
        self._queue = queue.Queue()
        self._running = False
        self.on_sentence_start = on_sentence_start
        self.on_sentence_end = on_sentence_end
    
    def speak(self, text: str):
        sentences = _split_sentences(text)
        for sentence in sentences:
            if not self._running:
                break
            self.on_sentence_start(sentence)
            # TTS çal
            self._play_sentence(sentence)
            self.on_sentence_end(sentence)
    
    def stop(self):
        """Barge-In: anında durdur."""
        self._running = False
        # Kuyruğu temizle
        while not self._queue.empty():
            self._queue.get_nowait()
```

### Ses Çıkış Cihazı Yönetimi

```python
# core/audio_system/audio_player.py
class AudioPlayer:
    """Cross-platform ses çalma."""
    
    def play_wav(self, path: str, blocking=False) -> bool:
        """WAV dosyası çal."""
        if sys.platform == "linux":
            subprocess.Popen(["aplay", path])
        elif os.name == "nt":
            subprocess.Popen(["powershell", "-c", 
                f"(New-Object Media.SoundPlayer '{path}').PlaySync()"])
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", path])
```

## Wake Word / VAD

### FahrettinVAD (`core/fahrettin_vad.py`)

```python
class FahrettinVAD:
    """
    Unified VAD wrapper — 3 backend:
    1. Silero VAD (PyTorch, en doğru)
    2. WebRTC VAD (webrtcvad, hızlı)
    3. Energy VAD (numpy, her zaman fallback)
    """
    
    def is_speech(self, audio_bytes: bytes, sample_rate: int) -> tuple[bool, float]:
        """Ses var mı? → (bool, confidence)"""
        if self._engine == "silero" and self._silero:
            return self._check_silero(audio_bytes)
        elif self._engine == "webrtc" and self._webrtc:
            return self._check_webrtc(audio_bytes)
        return self._check_energy(audio_bytes)  # fallback
```

### Wake Word (`core/wake_word.py`)

Sadece Ollama modunda aktiftir. Gemini modunda sürekli dinleme vardır.

```
Ollama modu:  WakeWordEngine.detect() → eşleşme → _on_text_command()
Gemini modu:  Sürekli dinleme (her ses LLM'e gider)
```

## Sesli Düşünme (Thinking Audio)

JARVIS "düşünürken" kullanıcıya görsel feedback verir (Orb animasyonu):

- **THINKING state:** Altın renk, dönen segmentler
- **Ses efekti:** Yok (sessiz düşünme)
- **Barge-In:** Kullanıcı konuşursa düşünme kesilir

## Mikrofon & Ses Cihazı Yönetimi

### Donanım Tespiti (`core/hardware_detector.py`)

```python
class HardwareDetector:
    @staticmethod
    def check_audio() -> HardwareInfo:
        """OS seviyesinde ses giriş/çıkış tespiti."""
        import pyaudio
        p = pyaudio.PyAudio()
        input_devices = []
        output_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                input_devices.append(info)
            if info["maxOutputChannels"] > 0:
                output_devices.append(info)
        p.terminate()
        return HardwareInfo(...)
```

### Cihaz Çakışması Çözümü

- PortAudio sequential stream açma
- Thread-safe `_speaking_lock` ile race condition önleme
- `p.terminate()` garantili çağrı (finally bloğu)

[Bkz. UI_LAYER.md](UI_LAYER.md) | [Bkz. LLM_INTEGRATION.md](LLM_INTEGRATION.md) | [Bkz. ARCHITECTURE.md](ARCHITECTURE.md)
