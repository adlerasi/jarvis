# J.A.R.V.I.S — Yapilandirma Referansi

> Tum yapilandirma dosyalari, anahtarlar ve varsayilan degerler.

---

## Dosya Yapisi

```
config/
+-- api_keys.json         # API anahtarlari (gitignore, ZORUNLU)
+-- api_keys.example.json # API anahtarlari ornegi
+-- audio.yaml            # Ses yapilandirmasi
+-- wake_word.yaml        # Wake word yapilandirmasi

app_config.py             # Python tarafindaki config okuyucu
```

---

## API Anahtarlari (`config/api_keys.json`)

### Dosya Formati

```json
{
  "gemini_api_key": "AIzaSy...",
  "voice": "Charon",
  "backend_type": "gemini",
  "ollama_model": "qwen2.5:1.5b",
  "ollama_tts_voice": "piper-fahrettin",
  "youtube_api_key": "",
  "youtube_channel_handle": ""
}
```

### Anahtar Detaylari

| Anahtar | Zorunlu | Varsayilan | Aciklama |
|---------|---------|-----------|----------|
| `gemini_api_key` | Evet | `""` | Google Gemini AI API anahtari |
| `backend_type` | Hayir | `"gemini"` | `"gemini"` veya `"ollama"` |
| `voice` | Hayir | `"Charon"` | Gemini ses modeli |
| `ollama_model` | Hayir | `""` | Ollama model adi (orn: `qwen2.5:1.5b`) |
| `ollama_tts_voice` | Hayir | `"piper-fahrettin"` | Local TTS sesi |
| `youtube_api_key` | Hayir | `""` | YouTube Data API v3 anahtari |
| `youtube_channel_handle` | Hayir | `""` | Varsayilan YouTube kanal handle'i |

### Gemini Ses Modelleri

| Ses ID | Aciklama |
|--------|----------|
| `Charon` | Varsayilan, dogal ses |
| `Puck` | Enerjik ses |
| `Aoede` | Nazik ses |
| `Kore` | Dengeli ses |
| `Fenrir` | Kalin ses |
| `Leda` | Yumusak ses (kadin) |
| `Persephone` | Sicak ses (kadin) |
| `Orus` | Tok ses (erkek) |
| `Zephyr` | Hafif ses |

### TTS Sesleri (Ollama Modu)

| Ses ID | Aciklama | Bagimlilik |
|--------|----------|-----------|
| `piper-fahrettin` | Piper - Fahrettin (Yerel, Turkce) | voice/Fahrettin-TTS/ |
| `edge-ahmet` | Edge - Ahmet Neural (Turkce Erkek) | edge-tts CLI |
| `edge-emel` | Edge - Emel Neural (Turkce Kadin) | edge-tts CLI |
| `spd-say` | spd-say (Sistem Sesi) | speech-dispatcher |

---

## Ses Yapilandirmasi (`config/audio.yaml`)

```yaml
audio:
  # Mikrofon ayarlari
  sample_rate: 48000
  block_size: 480        # 10 ms @ 48kHz (RNNoise frame boyutu)
  channels: 1            # Mono
  dtype: "float32"

  # Gurtultu Bastirma
  noise_suppression:
    enabled: true
    library: "rnnoise"
    frame_size: 480
    bypass_on_error: true

  # VAD (Voice Activity Detection)
  vad:
    fahrettin:
      engine: "energy"          # silero / webrtc / energy
      energy_threshold: 50.0    # RMS esigi
      debug_log: false

  # Wake Word
  wake_word:
    model_path: "models/wake_word.tflite"
    threshold: 0.7
    apply_noise_suppression_before: true

  # STT (Speech-to-Text)
  stt:
    engine: "whisper"
    model: "base"
    apply_noise_suppression_before: true
```

### Ses Yapilandirma Parametreleri

| Anahtar | Varsayilan | Aciklama |
|---------|-----------|----------|
| `audio.sample_rate` | 48000 | Mikrofon ornekleme hizi (Hz) |
| `audio.block_size` | 480 | Ses blogu boyutu (10ms @ 48kHz) |
| `audio.channels` | 1 | Ses kanal sayisi (mono) |
| `audio.dtype` | "float32" | Ses veri tipi |
| `noise_suppression.enabled` | true | RNNoise gurultu bastirma aktif/pasif |
| `noise_suppression.library` | "rnnoise" | Gurultu bastirma kutuphanesi |
| `noise_suppression.frame_size` | 480 | RNNoise frame boyutu |
| `noise_suppression.bypass_on_error` | true | Hata durumunda bypass modu |
| `vad.fahrettin.engine` | "energy" | VAD motoru (silero/webrtc/energy) |
| `vad.fahrettin.energy_threshold` | 50.0 | RMS ses esigi |
| `vad.fahrettin.debug_log` | false | VAD debug loglari |
| `wake_word.model_path` | "models/wake_word.tflite" | Wake word model dosyasi |
| `wake_word.threshold` | 0.7 | Wake word esigi (0.0-1.0) |
| `wake_word.apply_noise_suppression_before` | true | RNNoise wake word oncesi uygulama |
| `stt.engine` | "whisper" | STT motoru (whisper/google) |
| `stt.model` | "base" | Whisper model boyutu |
| `stt.apply_noise_suppression_before` | true | RNNoise STT oncesi uygulama |

---

## Wake Word Yapilandirmasi (`config/wake_word.yaml`)

```yaml
# Varsayilan degerler (opsiyonel, override)
engine: "openwakeword"
wake_word: "jarvis"

openwakeword:
  sensitivity: 0.5
  custom_model: "models/wake_word/jarvis.tflite"

porcupine:
  access_key: ""
  sensitivity: 0.5

energy:
  threshold: 0.03
  min_duration_ms: 500
  cooldown_ms: 2000

sample_rate: 16000
frame_duration_ms: 30
silence_timeout_ms: 5000
hold_time_ms: 200
require_hold: true
```

---

## AppConfig Python API (`app_config.py`)

### Fonksiyonlar

| Fonksiyon | Donus | Aciklama |
|-----------|-------|----------|
| `load_app_config()` | `dict` | JSON'dan config oku + DEFAULT ile merge |
| `save_app_config(updates)` | `dict` | JSON'a guncelleme yaz |
| `get_app_config_value(key, default)` | `Any` | Tek anahtar oku |
| `has_gemini_api_key()` | `bool` | API anahtari var mi? |
| `get_ollama_models()` | `list[str]` | localhost:11434/api/tags sorgula |
| `get_ollama_tts_voices()` | `list[dict]` | Kullanilabilir TTS seslerini listele |

### Varsayilan Config

```python
DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
    "backend_type": "gemini",
    "ollama_model": "",
    "ollama_tts_voice": "piper-fahrettin",
}
```

---

## UI Ayarlari

UI ayarlari uygulama ici `Settings` panelinden yapilir (config/api_keys.json'a yazilir):

- **Backend**: Gemini / Ollama secimi
- **Voice**: Gemini ses modeli secimi (Charon, Puck, Aoede, Kore, vb.)
- **Ollama Model**: Yerel model secimi
- **Ollama TTS Voice**: Yerel TTS sesi secimi

---

## Log Yapilandirmasi

Loglar `logs/jarvis.log` dosyasina yazilir:

| Ayar | Deger |
|------|-------|
| Hedef | `logs/jarvis.log` |
| Seviye | `DEBUG` |
| Format | `%(asctime)s - %(threadName)s - %(levelname)s - %(message)s` |
| httpcore | `WARNING` (gereksiz DEBUG'leri kapatir) |

Exception loglari ayrica `handle_exception()` ve `handle_thread_exception()` ile
stack trace olarak da kaydedilir.
