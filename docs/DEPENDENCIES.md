# J.A.R.V.I.S — Bağımlılıklar ve Kurulum

> Sistem gereksinimleri, Python paketleri, üçüncü taraf araçlar ve kurulum adımları.

---

## 🖥 Sistem Gereksinimleri

### Minimum

| Bileşen | Değer |
|---------|-------|
| Python | 3.10+ (3.13 önerilir) |
| RAM | 4 GB (Gemini modu), 8 GB (Ollama + local STT) |
| Disk | 2 GB boş alan (modellerle birlikte ~4 GB) |
| Ses | Mikrofon + hoparlör/kulaklık |
| İşletim Sistemi | Windows 10/11, Linux (Ubuntu 24+, Debian 12+), macOS |

### Önerilen

| Bileşen | Değer |
|---------|-------|
| Python | 3.13 |
| RAM | 16 GB |
| Disk | 8 GB boş alan |
| GPU | NVIDIA CUDA (faster-whisper hızlandırma için) |
| İnternet | Gemini backend için gerekli |

---

## 📦 Python Paketleri

### Zorunlu (Core)

Bu paketler olmadan uygulama çalışmaz:

| Paket | Sürüm | Kullanım | Modül |
|-------|-------|----------|-------|
| `google-genai` | >=1.0.0 | Gemini AI API (yeni SDK) | `core/multimodal.py`, `main.py` |
| `google-generativeai` | >=0.8.0 | Gemini AI API (eski SDK fallback) | `core/multimodal.py` |
| `SpeechRecognition` | >=3.10.0 | Ses tanıma (Google STT) | `core/audio_system/stt_engine.py` |
| `pyaudio` | >=0.2.13 | Ses giriş/çıkış (PortAudio) | `core/gemini_provider.py` |
| `sounddevice` | >=0.4.6 | Ses giriş/çıkış (alternatif) | `audio/microphone.py` |
| `faster-whisper` | >=1.0.0 | Yerel STT (Whisper) | `core/streaming_stt.py` |
| `httpx` | >=0.27.0 | Ollama HTTP API istemcisi | `core/ollama_provider.py` |
| `psutil` | >=5.9.0 | Sistem bilgisi (CPU/RAM/disk) | `actions/sys_info.py` |
| `Pillow` | >=10.0.0 | Görsel işleme (UI, ekran analizi) | `ui.py`, `core/multimodal.py` |
| `requests` | >=2.31.0 | HTTP istekleri | `actions/weather.py` |
| `numpy` | >=1.26.0 | Ses işleme, matematik | `core/ollama_provider.py` |
| `scipy` | >=1.10.0 | Ses yeniden örnekleme | `core/ollama_provider.py` |
| `pyyaml` | >=6.0 | YAML yapılandırma | `config/audio.yaml` |

### Opsiyonel (Özellik Bazlı)

Bu paketler eksikse ilgili özellik çalışmaz, uygulama bypass eder:

| Paket | Sürüm | Özellik | Eksikse |
|-------|-------|---------|---------|
| `openwakeword` | >=0.4.0 | Wake word (birincil) | Porcupine veya energy fallback |
| `pvporcupine` | >=3.0.0 | Wake word (Picovoice) | Energy fallback |
| `webrtcvad` | >=2.0.6 | VAD (WebRTC) | Energy VAD kullanılır |
| `torch` | >=2.0.0 | Silero VAD (~2 GB) | WebRTC veya Energy VAD |
| `pyautogui` | >=0.9.54 | Ekran/fare/klavye | Elle kullanım |
| `opencv-python` | >=4.8.0 | Kamera yakalama | Kamera özellikleri devre dışı |
| `watchdog` | >=4.0.0 | Dosya izleyici | File watcher devre dışı |
| `pywebview` | >=4.0 | Web UI arayüzü | Web UI çalışmaz |
| `pyttsx3` | >=2.90 | TTS (offline) | edge-tts veya gTTS kullanılır |
| `gTTS` | >=2.3.0 | TTS (Google) | Piper veya edge-tts kullanılır |

### Geliştirme

| Paket | Sürüm | Kullanım |
|-------|-------|----------|
| `basedpyright` | >=1.39.0 | LSP tip kontrolü |

---

## 🔧 Üçüncü Taraf Araçlar

Bu araçlar pip ile kurulamaz, ayrıca yüklenmeleri gerekir:

| Araç | Sürüm | Kullanım | Kurulum |
|------|-------|----------|---------|
| **Ollama** | >=0.1.0 | Yerel LLM backend | [ollama.ai](https://ollama.ai) |
| **RNNoise** | - | Gürültü bastırma (C kütüphanesi) | `python scripts/install_rnnoise.py` |
| **Piper TTS** | - | Yerel TTS (Fahrettin sesi) | Otomatik (`voice/Fahrettin-TTS/`) |
| **edge-tts** | - | Microsoft Neural TTS | `pip install edge-tts` veya sistem paketi |
| **ffmpeg** | >=4.0 | Ses dönüşümü | `apt install ffmpeg` veya [ffmpeg.org](https://ffmpeg.org) |

---

## 📥 Kurulum Adımları

### 1. Repoyu Klonla

```bash
git clone <repo-url> jarvis
cd jarvis
```

### 2. Sanal Ortam Oluştur

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Python Bağımlılıklarını Yükle

```bash
pip install -r requirements.txt
```

Opsiyonel paketleri de yüklemek için:
```bash
pip install openwakeword pvporcupine webrtcvad watchdog pyautogui
```

### 4. RNNoise Kütüphanesi

```bash
python scripts/install_rnnoise.py
```

Bu betik, işletim sistemine göre prebuilt RNNoise binary'sini indirir
ve `audio/lib/` altına yerleştirir. Başarısız olursa uygulama
gürültü bastırmasız çalışmaya devam eder.

### 5. API Anahtarları

`config/api_keys.json` oluşturun:

```json
{
  "gemini_api_key": "AIzaSy...",
  "backend_type": "gemini",
  "ollama_model": "qwen2.5:1.5b",
  "ollama_tts_voice": "piper-fahrettin"
}
```

### 6. Ses Modelleri (Opsiyonel)

**faster-whisper** modeli ilk çalıştırmada otomatik indirilir (`base` boyut).
**Fahrettin TTS** modeli `voice/Fahrettin-TTS/` altında olmalıdır.

### 7. Kurulumu Doğrula

```bash
python -m unittest tests.test_smoke -v
```

---

## 🐳 Docker (Planlanan)

Docker desteği gelecek sürümde eklenecektir.

---

## 🔄 Bağımlılık Güncelleme

Mevcut bağımlılıkları güncellemek için:

```bash
pip install --upgrade -r requirements.txt
```

Yeni bir bağımlılık eklendiğinde:
1. Gereksinimi `requirements.txt`'e ekle
2. `docs/DEPENDENCIES.md`'yi güncelle
3. Kategoriyi doğru belirle (zorunlu/opsiyonel/geliştirme)

---

## 📚 İlgili Dokümantasyon

| Dosya | Açıklama |
|-------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Sistem Mimarisi |
| [CONFIG.md](CONFIG.md) | Yapılandırma Sistemi |
| [API_REFERENCE.md](API_REFERENCE.md) | Dahili API Referansı |
