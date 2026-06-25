# J.A.R.V.I.S — Windows Sesli Asistan

> **J**ust **A** **R**ather **V**ery **I**ntelligent **S**ystem  
> Adler ASİ tarafından yapılmıştır · İyilik iyidir...

Gerçek zamanlı, sesle çalışan, yapay zeka destekli kişisel asistan.  
Google Gemini AI (birincil) veya Ollama (yerel) backend ile çalışır.

---

## ✨ Özellikler

| Özellik | Açıklama |
|---------|----------|
| **🎤 Sesli Konuşma** | Gerçek zamanlı mikrofon girişi, Gemini Audio API ile doğal diyalog |
| **🔇 Gürültü Bastırma** | RNNoise ile gerçek zamanlı gürültü bastırma (48kHz/16kHz), bypass modu |
| **🤖 Çift Backend** | Gemini AI (bulut) veya Ollama (yerel, offline) desteği |
| **🎨 Tkinter UI** | Özel tasarım konsantrik halka animasyonu, durum göstergeleri |
| **📂 Uygulama Açma** | 50+ Windows uygulaması için alias sistemi ile hızlı erişim |
| **📅 Takvim Yönetimi** | Windows takviminden etkinlik okuma/ekleme/silme |
| **🔔 Hatırlatıcılar** | Yerel hatırlatıcı ekleme ve listeleme |
| **🌤 Hava Durumu** | wttr.in API ile anlık hava durumu sorgulama |
| **💬 WhatsApp** | WhatsApp Web/Desktop üzerinden mesaj gönderme |
| **📺 YouTube Analizi** | Kanal istatistikleri, video performans raporu |
| **🖥 Ekran Analizi** | Aktif pencere ekran görüntüsü + Gemini Vision analizi |
| **🧠 Kalıcı Bellek** | Kullanıcı bilgilerini JSON dosyasında saklama |
| **🔧 Shell Komutları** | Güvenlik filtreli komut çalıştırma |
| **🧩 Skill Sistemi** | AI'sız doğrudan işlem, anında yanıt, aç/kapa/ara komutları |
| **🌐 Tarayıcı Kontrolü** | URL açma, Google arama, YouTube oynatma |
| **🎵 Medya Oynatma** | YouTube/Spotify/Apple Music desteği |
| **🔊 Çoklu TTS** | Piper (yerel), Edge-TTS (bulut), Windows Speech |
| **🩺 Sistem Kontrolü** | Sistem sağlığı, disk temizlik, süreç yönetimi, ağ izleme |
| **⏰ Zamanlanmış Görevler** | Cron benzeri görev zamanlama ve yönetim |
| **🔍 Dosya Yönetimi** | Büyük dosya bulma, yinelenen dosya tespiti, klasör temizlik |
| **📡 Ağ İzleme** | Bağlantı listesi, ping testi, bant genişliği takibi |
| **🛠 Servis Yönetimi** | Windows servislerini listeleme/kontrol |

---

## 🚀 Hızlı Kurulum

### Gereksinimler

- Python 3.10+ (3.13 önerilir)
- Windows 10/11, Linux (test: Ubuntu 24+, Debian 12+), macOS
- Ses giriş/çıkış donanımı
- İnternet bağlantısı (Gemini modu için)

### 1. Depoyu Klonla

```powershell
git clone <repo-url> jarvis
cd jarvis
```

### 2. Sanal Ortam Oluştur

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Bağımlılıkları Yükle

```powershell
pip install -r requirements.txt
```

### 4. API Anahtarını Yapılandır

`config/api_keys.json` dosyasına Gemini API anahtarını gir:

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

Alternatif: `config/api_keys.example.json` dosyasını kopyalayıp düzenleyin.

### 5. RNNoise Gürültü Bastırma (opsiyonel)

```bash
python scripts/install_rnnoise.py
```

Bu betik, RNNoise C kütüphanesini otomatik olarak indirir veya kaynaktan derler (`audio/lib/librnnoise.so`).  
Kütüphane bulunamazsa JARVIS sessizce bypass modunda çalışır — gürültü bastırma olmaz, ama uygulama kesintisiz devam eder.

### 6. Otomatik Kurulum (opsiyonel)

```powershell
.\setup.ps1
```

---

## 🎮 Kullanım

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

### UI Kontrolleri

| Kontrol | İşlev |
|---------|-------|
| 🟢 Dinleme modu | Mikrofon açık, komut bekliyor |
| 🔵 Konuşma modu | JARVIS yanıt veriyor |
| 🟡 Düşünme modu | İşlem yapılıyor |
| 🔴 Hata | Bir sorun oluştu |
| 🟣 Sessiz | Ses çıkışı kapalı |
| ⚪ Duraklatıldı | Tüm işlemler durdu |

---

## 📁 Dizin Yapısı

```
jarvis/
├── main.py                  # Ana uygulama — JARVIS çekirdeği
├── ui.py                    # Tkinter UI — konsantrik halka arayüz
├── app_config.py            # Yapılandırma yönetimi
├── setup.ps1                # Windows kurulum betiği
├── requirements.txt         # Python bağımlılıkları
├── .gitignore               # Git yok sayma kuralları
│
├── audio/                   # Ses işleme modülü
│   ├── __init__.py          # Paket ihracatı (NoiseSuppressor, MicrophoneStream)
│   ├── noise_suppressor.py  # RNNoise gerçek zamanlı gürültü bastırma (271 satır)
│   ├── microphone.py        # Sounddevice mikrofon akışı + RNNoise entegrasyonu
│   └── lib/                 # RNNoise C kütüphanesi (librnnoise.so)
│
├── actions/                 # İşlem modülleri
│   ├── open_app.py          # Uygulama açma (50+ alias)
│   ├── sys_info.py          # Sistem bilgisi (CPU/RAM/disk/batarya)
│   ├── weather.py           # Hava durumu (wttr.in)
│   ├── calendar.py          # Windows takvim yönetimi
│   ├── reminders.py         # Hatırlatıcı yönetimi
│   ├── browser.py           # Tarayıcı kontrolü
│   ├── shell.py             # Güvenli shell komutları
│   ├── whatsapp.py          # WhatsApp mesajlaşma
│   ├── media.py             # Medya oynatma
│   ├── youtube_stats.py     # YouTube kanal analizi
│   ├── screen_vision.py     # Ekran görüntüsü + Vision AI
│   ├── tts.py               # Text-to-Speech (3 backend)
│   ├── windows_utils.py     # Windows API araçları
│   ├── health.py            # Platform sağlık verisi
│   ├── system_doctor.py     # Sistem sağlık raporu
│   ├── process_manager.py   # Süreç yönetimi
│   ├── file_guardian.py     # Dosya yönetimi
│   ├── network_monitor.py   # Ağ izleme
│   ├── system_cron.py       # Zamanlanmış görevler
│   ├── service_monitor.py   # Servis yönetimi
│   ├── disk_predictor.py    # Disk doluluk tahmini
│   ├── process_timeline.py  # Süreç zaman çizelgesi
│   ├── network_anomaly.py   # Ağ anomali tespiti
│   ├── cron_web_ui.py       # Cron web arayüzü
│   └── watchdog/            # Dosya sistemi izleyici
│       └── file_watcher.py  # Gerçek zamanlı dosya izleme
│
├── core/                    # Çekirdek
│   ├── provider_base.py     # Abstract BaseProvider arayüzü
│   ├── gemini_provider.py   # Gemini Live API provider
│   ├── ollama_provider.py   # Ollama HTTP provider (STT + chat + TTS)
│   ├── tool_registry.py     # 40 tool tek kaynağı (declarations + handler map)
│   ├── text_utils.py        # Metin işleme (transcript temizleme, hece bölme)
│   ├── prompt.txt           # Sistem prompt'u
│   └── skill_manager.py     # Skill yükleyici & router
│
├── skills/                  # Skill modülleri (AI'sız doğrudan işlem)
│   ├── browser/             # Tarayıcı kontrolü
│   ├── system_health/       # Sistem sağlığı kontrolü
│   ├── process_control/     # Süreç yönetimi
│   ├── file_manager/        # Dosya yönetimi
│   ├── network/             # Ağ izleme
│   ├── scheduler/           # Zamanlanmış görevler
│   ├── services/            # Servis yönetimi
│   ├── weather/             # Hava durumu sorgulama
│   ├── youtube/             # YouTube kanal istatistikleri + oynatma
│   ├── vision/              # Ekran görüntüsü analizi
│   ├── calendar/            # Takvim yönetimi
│   ├── reminders/           # Hatırlatıcı yönetimi
│   ├── whatsapp/            # WhatsApp mesajlaşma
│   └── media/               # Medya oynatma
│
├── config/                  # Yapılandırma
│   ├── api_keys.json        # API anahtarları (gitignore)
│   ├── api_keys.example.json
│   └── audio.yaml           # Ses yapılandırması (RNNoise, sample rate)
│
├── memory/                  # Kalıcı bellek
│   ├── memory_manager.py    # Bellek yönetimi
│   ├── health/              # Sağlık verileri
│   └── *.json               # Kullanıcı belleği
│
├── voice/                   # Ses modelleri
│   ├── faster-whisper/      # STT modeli (~464MB)
│   ├── faster-whisper-large-backup/  # Yedek model (~1.6GB)
│   └── Fahrettin-TTS/       # Piper TTS modeli (~61MB)
│
├── Icon/                    # UI ikonları
│   ├── instagram-logo.png
│   └── youtube-logo.png
│
├── SFX/                     # Ses efektleri
│   └── HUD.mp3
│
├── Fonts/                   # Özel fontlar
├── helpers/bin/             # Binary bağımlılıklar
├── tests/                   # Testler
│   ├── test_smoke.py        # 2512 test (81 dosya, smoke + unit)
│   ├── test_system_doctor.py
│   ├── test_process_manager.py
│   ├── test_file_guardian.py
│   ├── test_network_monitor.py
│   ├── test_system_cron.py
│   ├── conftest.py          # Test yapılandırması
│   └── __init__.py
└── logs/                    # Uygulama logları
    └── jarvis.log
```

---

## ⚙️ Yapılandırma

### API Anahtarları (`config/api_keys.json`)

| Anahtar | Zorunlu | Açıklama |
|---------|---------|----------|
| `gemini_api_key` | ✅ | Gemini AI API anahtarı (birincil backend) |
| `voice` | ❌ | Gemini ses modeli (varsayılan: `Charon`) |
| `backend_type` | ❌ | `gemini` veya `ollama` (varsayılan: `gemini`) |
| `ollama_model` | ❌ | Ollama model adı (örn: `qwen2.5:1.5b`) |
| `ollama_tts_voice` | ❌ | Yerel TTS sesi (varsayılan: `piper-fahrettin`) |
| `youtube_api_key` | ❌ | YouTube Data API anahtarı |
| `youtube_channel_handle` | ❌ | YouTube kanal handle'ı |

### UI Yapılandırması

UI ayarları uygulama içi `Settings` panelinden yapılır:
- **Backend**: Gemini / Ollama seçimi
- **Voice**: Ses modeli seçimi (Charon, Puck, Aoede, Kore, vb.)
- **Ollama Model**: Yerel model seçimi
- **Ollama TTS Voice**: Yerel TTS sesi seçimi

---

## 🔧 Geliştirici Bilgisi

### Kod İstatistikleri

| Ölçüt | Değer |
|-------|-------|
| Toplam Python satırı | ~11,000+ |
| Python dosyası | 45+ |
| Action modülü | 20 |
| Audio modülü | 3 (noise_suppressor, microphone, lib) |
| Skill modülü | 17 |
| Test sayısı | 2512 (unittest, 1 failure, 4 skip) |
| UI satırı | ~2,300 |
| Ana çekirdek | ~2,000 |

### Test

```bash
python -m unittest discover tests -v
```

### LLM Kullanımı

Bu proje [OhMyOpenCode](https://github.com/ohmyopenopencode/opencode) (Sisyphus) ile geliştirilmiştir.
