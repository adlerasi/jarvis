# J.A.R.V.I.S — Ses İşleme Hattı (Audio Pipeline)

> RNNoise gürültü bastırma → VAD → Wake Word → STT (faster-whisper) → TTS zinciri.

---

## 🏗 Genel Mimari

```
Mikrofon
   │
   ▼
┌────────────────────────────────────────────────────────────┐
│                 SES İŞLEME HATTI (Audio Pipeline)           │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Mikrofon Yakalama                                        │
│     ├── pyaudio (PortAudio, varsayılan)                     │
│     └── sounddevice (alternatif, audio/microphone.py)       │
│         └── MicrophoneStream (context manager)              │
│                                                             │
│  2. RNNoise Gürültü Bastırma (audio/noise_suppressor.py)    │
│     ├── 48kHz native mod: direct RNNoise processing         │
│     ├── 16kHz mod: upscale → RNNoise → downscale           │
│     └── bypass: library yoksa direkt geçir                  │
│                                                             │
│  3. Yönlendirme                                              │
│     ├── GEMINI → pyaudio stream (16kHz) → Gemini Live API   │
│     └── OLLAMA → VAD + STT + LLM + TTS                      │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 Bileşen Detayları

### 1. Mikrofon Yakalama

**Dosya**: `audio/microphone.py`

```
MicrophoneStream (context manager)
├── __init__(sample_rate=16000, channels=1, dtype="float32")
│   └── sounddevice.InputStream callback
├── __enter__ / __exit__ → stream aç/kapa
├── read() → numpy array (float32)
└── Ornek:
    with MicrophoneStream(sample_rate=16000) as mic:
        while True:
            chunk = mic.read()  # 30ms chunk
            process(chunk)
```

**Kullanım**: 
- Ollama modu: `audio/microphone.py` → VAD → faster-whisper
- Gemini modu: `pyaudio` direct → Gemini Live API

### 2. RNNoise Gürültü Bastırma

**Dosya**: `audio/noise_suppressor.py` (271 satır)

```
NoiseSuppressor
├── __init__(sample_rate=48000, enabled=True, lib_dir=None)
│   ├── Yüklenebilirse → ctypes.CDLL("librnnoise.so") → DenoiseState oluştur
│   └── Yüklenemezse → enabled=False (bypass modu)
│
├── process_frame(noisy_frame: np.ndarray[int16]) → np.ndarray[int16]
│   └── 48000 Hz için: (480,) int16 → RNNoise → (480,) int16
│
├── process_16khz(noisy_frame: np.ndarray[int16]) → np.ndarray[int16]
│   └── 16000 Hz için: (480,) int16 → (480,) float32 → resample to 48kHz
│       → RNNoise işleme (VAD prob + gürültü bastırma)
│       → resample to 16kHz → (480,) int16
│
├── process_stream(frames: np.ndarray[int16]) → np.ndarray[int16]
│   └── Çoklu frame işleme (vectorized)
│
├── get_vad_probability() → float
│   └── RNNoise iç VAD olasılığı (0.0-1.0)
│
├── reset() → DenoiseState sıfırla
│
├── enabled: bool
├── sample_rate: int
└── lib_dir: Path | None
```

**Kütüphane Yükleme Stratejisi**:

```
librnnoise.so aranma sırası:
1. audio/lib/librnnoise.so (proje yerel)
2. LD_LIBRARY_PATH
3. Sistem kütüphane yolları (/usr/lib, /usr/local/lib)
4. pip install rnnoise ile gelen kütüphane
```

**Desteklenen Örnek Hızları**: 48000, 44100, 22050, 16000 Hz

### 3. VAD Sistemi

**Dosyalar**: `core/fahrettin_vad.py` (193 satır), `core/vad_engine.py` (325 satır)

```
FahrettinVAD (Unified Wrapper)
├── is_speech(audio_bytes, sample_rate) → (bool, confidence)
│   └── Auto-downsample 48kHz → 16kHz
│   └── Thread-safe
│
├── get_debug_stats() → dict
│   └── {"rms": 0.05, "noise_floor": 0.01, "speech_ratio": 0.3, ...}
│
├── reset()
│
└── VADEngine (Arka Uç)
    ├── Silero VAD (torch) → WebRTC (webrtcvad) → Energy (numpy)
    ├── State machine: SPEECH / SILENCE / PADDING
    └── Frame size: sample_rate * frame_duration_ms / 1000
```

**VAD Karar Mekanizması**:

```
Gelen ses çerçevesi (30ms @ 16kHz)
         │
         ▼
    RMS Hesapla
         │
    ┌────┴────┐
    │ < eşik  │───→ SESSİZLİK
    └────┬────┘
         │ ≥ eşik
         ▼
    ┌──────────┐
    │ Silero   │───→ varsa torch tahmini
    └────┬─────┘
         │
    ┌────┴────┐
    │ WebRTC  │───→ varsa webrtcvad tahmini
    └────┬─────┘
         │
         ▼
    Energy fallback (her zaman var)
         │
         ▼
    State Machine
    ├── min_speech_duration_ms=250
    ├── min_silence_duration_ms=800
    ├── speech_pad_ms=300
    └── silence_timeout_ms=5000
```

### 4. Wake Word Sistemi

**Dosya**: `core/wake_word.py` (259 satır)

```
WakeWordEngine
├── Zincir: openWakeWord → Porcupine → Energy
├── detect(audio_frame) → bool
├── set_activation_callback(fn)
├── set_deactivation_callback(fn)
└── Sadece Ollama modunda aktiftir
```

### 5. STT (Speech-to-Text)

**Dosyalar**: `core/streaming_stt.py` (300 satır), `core/audio_system/stt_engine.py`

```
Streaming STT Pipeline:

Ses → VAD → Speech Buffer → faster-whisper → Türkçe Düzeltme → Metin
                               │                    │
                               ▼                    ▼
                        WhisperModel          text_utils.py
                        .transcribe()         ├── NFC normalize
                                              ├── fix_turkish_syllable_split()
                                              └── clean_transcript_text()
```

**STT Engine (core/audio_system/stt_engine.py)**:

| Engine | Bağımlılık | Hız | Doğruluk | İnternet |
|--------|-----------|-----|----------|---------|
| Google STT | `SpeechRecognition` | Hızlı | ★★★★ | Gerekli |
| faster-whisper | `faster-whisper` ~464MB | Orta | ★★★★ | Hayır |
| Whisper large | `faster-whisper` ~1.6GB | Yavaş | ★★★★★ | Hayır |

### 6. TTS (Text-to-Speech)

**Dosya**: `core/audio_system/tts_engine.py` (457 satır)

```
TTS Zinciri (Fallback):

LLM Yanıtı
    │
    ▼
┌─────────────┐
│ Piper       │──→ echo "metin" | piper --model ... --output-raw | aplay
│ (yerel)     │    tr_TR-fahrettin-medium.onnx (~61MB)
└──────┬──────┘
       │ başarısız
       ▼
┌─────────────┐
│ pyttsx3     │──→ pyttsx3.init() → engine.say()
│ (offline)   │    Cross-platform, düşük kalite
└──────┬──────┘
       │ başarısız
       ▼
┌─────────────┐
│ edge-tts    │──→ edge-tts --voice ... --text ... --write-media out.mp3
│ (Microsoft) │    tr-TR-AhmetNeural / tr-TR-EmelNeural
└──────┬──────┘
       │ başarısız
       ▼
┌─────────────┐
│ gTTS        │──→ gTTS(text=..., lang="tr") → mp3
│ (Google)    │    İnternet gerekli
└──────┬──────┘
       │ başarısız
       ▼
  spd-say (son fallback, Linux)
```

### 7. Audio Player

**Dosya**: `core/audio_system/audio_player.py`

```
AudioPlayer (singleton)
├── play_wav(path, blocking=False) → bool
├── play_bytes(data, sample_rate, blocking=False) → bool
├── stop()
└── Destek: aplay (Linux) / ffplay (cross) / PowerShell (Windows)
```

---

## 🔄 Gemini Backend Ses Akışı

```
pyaudio.InputStream (16kHz)
    │
    ├── out_queue → Gemini Live API (send_realtime_input)
    │   └── Maxsize=10 (backpressure)
    │
    ├── local VAD → ses seviyesi göstergesi
    │
    └── Wake Word (Ollama modunda)

Gemini Live API (receive)
    │
    ├── audio_in_queue → pyaudio.OutputStream (24kHz)
    │   └── Hoparlör
    │
    └── text → transcript → tool calls
```

**Thread Modeli** (Gemini modu, 4 eşzamanlı coroutine):

```
TaskGroup:
├── _send_realtime()    → ses gönderme
├── _listen_audio()     → mikrofon okuma + wake word
├── _receive_audio()    → yanıt alma + tool call işleme
└── _play_audio()       → ses çalma
```

---

## 🔄 Ollama Backend Ses Akışı

```
Mikrofon → pyaudio InputStream (16kHz)
    │
    ├── RNNoise.process_16khz() → gürültü bastırma
    │
    ├── WakeWordEngine.detect() → wake word bekleme
    │
    ├── VAD → Speech Buffer (konuşma algılanana kadar bekle)
    │
    ├── faster-whisper → transkripsiyon
    │   └── fix_turkish_syllable_split()
    │   └── clean_transcript_text()
    │
    ├── _on_text_command()
    │   ├── skill_manager.route() → skill eşleşirse direkt yanıt
    │   └── Ollama HTTP /api/chat → LLM yanıtı
    │       └── tool call'lar → _execute_tool()
    │
    └── TTS → Hoparlör
```

---

## 🎛 Konfigürasyon

**Dosya**: `config/audio.yaml`

```yaml
audio:
  sample_rate: 48000
  block_size: 480        # 10 ms @ 48kHz
  channels: 1

  noise_suppression:
    enabled: true
    library: "rnnoise"
    frame_size: 480
    bypass_on_error: true

  vad:
    fahrettin:
      engine: "energy"
      energy_threshold: 50.0
      debug_log: false

  wake_word:
    model_path: "models/wake_word.tflite"
    threshold: 0.7
    apply_noise_suppression_before: true

  stt:
    engine: "whisper"
    model: "base"
    apply_noise_suppression_before: true
```

---

## 📊 Performans Metrikleri

| Aşama | Gecikme | İşlemci |
|-------|---------|---------|
| RNNoise (1 frame) | ~0.3ms | CPU |
| VAD (energy) | ~0.1ms | CPU |
| VAD (Silero) | ~5ms | GPU/CPU |
| Wake word (openWakeWord) | ~10ms | CPU |
| STT (faster-whisper base) | ~100-300ms | GPU/CPU |
| STT (faster-whisper large) | ~1-3s | GPU |
| TTS (Piper) | ~50ms | CPU |
| TTS (edge-tts) | ~500ms-1s | Ağ |
| Ollama LLM | ~500ms-5s | GPU/CPU |
| Gemini API | ~200ms-2s | Ağ |

---

## 🔊 Ses Seviyesi Yönetimi

**Dosya**: `main.py` (`_set_volume`, `_set_volume_windows`, `_set_volume_macos`, `_set_volume_linux`)

| Platform | Yöntem |
|----------|--------|
| Windows | `nircmd.exe setvolume` |
| macOS | `osascript -e "set volume output volume X"` |
| Linux | `pactl set-sink-volume @DEFAULT_SINK@ X%` |
