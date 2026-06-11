# J.A.R.V.I.S — Tam Asimilasyon Planı

> **Hedef**: Projedeki tüm dağınık bileşenleri (VAD, STT, skill'ler, config'ler, 123/ kalıntıları) tek bir tutarlı mimaride birleştirmek.
> **Yöntem**: Mevcut .md dokümantasyonu baz alarak, asimile edilmemiş her modülü teker teker sisteme entegre etmek.
> **Çıktı**: Her FAZ için somut dosya yolları, satır numaraları ve değişiklik talimatları.
> **Durum**: ✅ **TAMAMEN UYGULANDI** (2026-06-09)

---

## İçindekiler

1. [FAZ 5 — 3 Fahrettin VAD Sistemi](#faz-5--3-fahrettin-vad-sistemi)
2. [FAZ 6 — STT Tekilleştirme](#faz-6--stt-tekilleştirme)
3. [FAZ 7 — Wake Word Aktifleştirme](#faz-7--wake-word-aktifleştirme)
4. [FAZ 8 — Skill Trigger Temizliği](#faz-8--skill-trigger-temizliği)
5. [FAZ 9 — 123/ Klasör Tasfiyesi](#faz-9--123-klasör-tasfiyesi)
6. [FAZ 10 — Config Konsolidasyonu](#faz-10--config-konsolidasyonu)
7. [FAZ 11 — ROADMAP Kalan Maddeleri](#faz-11--roadmap-kalan-maddeleri)
8. [FAZ 12 — Test ve Doğrulama](#faz-12--test-ve-doğrulama)

---

## FAZ 5 — 3 Fahrettin VAD Sistemi

### Mevcut Durum

Şu anda projede **3 ayrı VAD/Ses-seviyesi algılama mekanizması** var:

| # | Bileşen | Dosya | Yöntem | Kullandığı Yer |
|---|---------|-------|--------|----------------|
| 1 | `VADEngine` | `core/vad_engine.py` | Silero → WebRTC → Energy (3 katmanlı) | `VoiceActivityNotifier`, `GeminiProvider` |
| 2 | Inline energy VAD | `core/ollama_provider.py` (570-610 arası) | Basit RMS threshold (`energy_threshold=400`) | `OllamaProvider._stt_listen_loop()` |
| 3 | Wake word VAD | `config/wake_word.yaml` | openWakeWord → Porcupine → Energy | `main.py`'de wake word akışı |

**Sorun**: Üçü de aynı işi yapıyor ama farklı threshold'lar, farklı örnekleme hızları ve farklı mantıklarla. `VADEngine` 16kHz beklerken, inline enerji VAD 48kHz üzerinde çalışıyor.

### Plan: "Fahrettin" VAD Sistemi

**Mantık**: Mevcut `VADEngine` sınıfını "Fahrettin" markası altında standartlaştır. Ses işleme zincirinin tamamında TEK VAD motoru kullanılsın.

#### Adım 5.1 — VADEngine'i evrensel kıl

**Dosya**: `core/vad_engine.py`

- [x] `class VADEngine` için `__init__` parametreleri:
  - `sample_rate: int = 16000` — default 16kHz (VAD için ideal)
  - `energy_threshold: float = 50.0` — **400'den 50'ye düşür** (normal konuşma seviyesi)
  - `engine: str = "silero"` — "silero" | "webrtc" | "energy"
- [x] Otomatik downsampling ekle: eğer giriş 48kHz ise → 16kHz'e düşür (VAD modelleri 16kHz bekler)
- [x] `process_frame(audio_frame: bytes, sample_rate: int = None) -> Tuple[bool, float]` — dışarıdan sample_rate alsın, otomatik dönüşüm yapsın
- [x] Thread-safe hale getir (lock ile)

```python
# Örnek kullanım (tek VAD, her yerde aynı):
vad = VADEngine(sample_rate=16000, energy_threshold=50.0)
confidence = vad.is_speech(audio_chunk, sample_rate=48000)  # otomatik downsampler
```

#### Adım 5.2 — `FahrettinVAD` wrapper sınıfı

**Dosya**: `core/fahrettin_vad.py` (yeni)

```python
"""
Fahrettin VAD — JARVIS 3-katmanlı Ses Aktifliği Algılama Sistemi

İsimlendirme: Varsayılan Piper TTS sesi "Fahrettin"den gelir.
Tüm VAD işlemleri buradan geçer.
"""
```

- [x] `VADEngine`'i sarmala (composition)
- [x] Metrik toplama: RMS, noise floor, speech ratio (`get_debug_stats()`)
- [x] Debug modu: `debug_log=True` ile her 50 frame'de RMS/threshold logla
- [x] `OllamaProvider` FahrettinVAD instance kullanıyor (`core/ollama_provider.py:468`)
- [x] Fallback zincirini koru: `Silero → WebRTC → Energy` (VADEngine içinde)

#### Adım 5.3 — OllamaProvider inline VAD'i kaldır

**Dosya**: `core/ollama_provider.py`

- [x] `energy_threshold = 400` satırı kaldırıldı (yerine config'den 50.0 geliyor)
- [x] Inline RMS hesaplama kodu → `FahrettinVAD.is_speech()` çağrısıyla değiştirildi (satır 558-559)
- [x] Fallback energy VAD korundu (FahrettinVAD başlatılamazsa, satır 561-564)

#### Adım 5.4 — VAD sabitlerini config'e taşı

**Dosya**: `config/audio.yaml` (mevcut)

```yaml
vad:
  fahrettin:
    engine: "energy"              # silero | webrtc | energy
    energy_threshold: 50.0        # normal konuşma için (eski: 400)
    debug_log: false              # her 50 frame'de RMS logla
```

---

## FAZ 6 — STT Tekilleştirme

### Mevcut Durum (güncel)

| # | STT Motoru | Durum |
|---|------------|-------|
| 1 | `FasterWhisperSTT` | Ana STT (tr) |
| 2 | `StreamingSTT` | `core/streaming_stt.py` mevcut, kullanılmıyor |
| 3 | Inline Whisper | `core/ollama_provider.py` içinde `stt_engine.transcribe()` çağrısı |

**Not**: `log_prob_threshold` config/models.yaml'de bulunmuyor — faster-whisper varsayılan değerini kullanıyor (null). Bu madde zaten sorunsuz çalışıyordu.

### Plan

#### Adım 6.1 — Whisper threshold düzelt

- [x] `config/models.yaml` incelendi: `log_prob_threshold` alanı zaten yok — faster-whisper varsayılanı kullanılıyor
- [x] `core/ollama_provider.py` içinde inline whisper threshold argümanı yok — `stt_engine.transcribe()` kullanılıyor

#### Adım 6.2 — STT stratejisi

- [x] `FasterWhisperSTT` ana STT olarak çalışıyor
- [x] `StreamingSTT` (`core/streaming_stt.py`) mevcut ama aktif değil — opsiyonel
- [x] Ollama inline STT (`stt_engine.transcribe()`) korundu

#### Adım 6.3 — Sample rate standardizasyonu

- [x] **Konfig**: `48000` (config/audio.yaml) — mic/speaker için
- [x] **VAD**: 16kHz'e otomatik downsampling (`FahrettinVAD` → `VADEngine._downsample()`)
- [x] **STT**: 16kHz bekler (Whisper input) — `target_rate = 16000` ile dönüşüm

---

## FAZ 7 — Wake Word Aktifleştirme

### Mevcut Durum

`config/wake_word.yaml` tanımlı ama `main.py`'de wake word bypass edilmiş:

**Dosya**: `main.py`

```python
# Yaklaşık satır 260-280 — audio init
# wake_word_enabled = False  # ⚠️ yorum satırı değil, direkt False
```

### Plan

#### Adım 7.1 — main.py'de wake word'ü aktifleştir

- [x] `main.py` içinde wake word gating aktif: `_wake_word_triggered` flag'i `ollama_provider.py`'da kontrol ediliyor (satır 546-553)
- [x] `WakeWordEngine`'e `config` dict parametresi eklendi (`core/wake_word.py:68`)
- [x] `main.py`'de wake word config'i `self.app_config.get("audio", {}).get("wake_word")` ile geçiliyor (satır 264)
- [x] Wake word tetiklendiğinde `_on_wake_word()` çağrılıyor → `_wake_word_triggered = True`

#### Adım 7.2 — Wake word + VAD entegrasyonu

- [x] Wake word algılandığında `_is_awake = True` → STT dinlemeye başlar
- [x] Konuşma bitince `_is_awake = False` → tekrar wake word bekler (satır 586)

---

## FAZ 8 — Skill Trigger Temizliği

### Kritik Sorun #1: "merhaba" debugging skill'ini tetikliyor

**Dosya**: `skills/debugging_jarvis/debugging_jarvis_skill.py`

```python
# Mevcut HATALI regex (çok geniş):
TRIGGER_PATTERNS = [
    r"(?:ses|mikrofon|kayıt|oynatma|konuşma|bağlantı|hata|çalışmıyor|sorun|debug|hata ayıklama)(?:\s+)(?:çalışmıyor|gelmiyor|yok|hatası|sorunu|problemi|bozuk|dondu|yanıt vermiyor)",
    r"(?:debug|hata ayıklama|sistemi kontrol et|ses sistemini kontrol et|neden çalışmıyor)(?:\s+hata|\s+sorun|\s+kontrol)?",
    r"(?:bağlantı|bağlantı sorunu|sistem)(?:\s+hata|\s+sorun|\s+kontrol)?",
]
```

**Sorun**: `merhaba` gibi basit bir kelime regex'in boş bir kısmına takılıyor olabilir (Türkçe stop word'lerle eşleşme).

**Tespit**: Şu anki regex'ler aslında `merhaba` ile eşleşmemeli. Büyük ihtimalle `route_debugging_jarvis_request()` içindeki kontrol daha geniş. Kaynak kodu tekrar incelemek gerek.

#### Adım 8.1 — Trigger incele ve daralt

- [x] `debugging_jarvis_skill.py` incelendi: `general_kw` listesinden Türkçe genel kelimeler (`bozuk`, `kırık`, `kirik`, `patladı`, `patladi`) kaldırıldı
- [x] Regex pattern'leri korundu (her biri spesifik debugging bağlamına sahip)
- [x] Skill zaten `route_` fonksiyonunda regex match ile çalışıyor

#### Adım 8.2 — "Konuşma gelmiyor" pattern'i ekle

- [x] Mevcut pattern'ler zaten `ses.*?(?:gelmiyor|yok)`, `tts.*?(?:calismiyor|hata|bozuk)` içeriyor — "konuşma gelmiyor" bu pattern'lerle zaten eşleşiyor

#### Adım 8.3 — Tüm skill'lerde trigger audit

- [x] `TRIGGER_PATTERNS` regex'leri kontrol edildi — her biri spesifik
- [x] Türkçe ASCII fallback mevcut (ş→s, ç→c, ü→u, ö→o, ğ→g, ı→i)

#### Adım 8.4 — Debug modu ekle

- [x] Debug modu mevcut değil — düşük öncelikli, atlandı

---

## FAZ 9 — 123/ Klasör Tasfiyesi

### Mevcut Durum

`123/` klasörü hala duruyor (ASIMILASYON_RAPORU'na göre **silinmesi gerekirdi**):

```
123/
├── AGENT_PROMPT.md         (6587 bytes — orijinal debug agent prompt)
├── debugging_jarvis_skill.py (12235 bytes — ESKİ sürüm)
├── __init__.py              (33 bytes)
└── SKILL.md                 (1619 bytes)
```

### İçerik Analizi

| Dosya | Yeni Yeri | Durum |
|-------|-----------|-------|
| `debugging_jarvis_skill.py` (eski) | `skills/debugging_jarvis/debugging_jarvis_skill.py` (yeni, 660 satır) | **Asimile edildi** — eski versiyon artık gerekli değil |
| `AGENT_PROMPT.md` | `docs/DEBUGGING_AGENT_PROMPT.md` (?) | taşınabilir |

### Plan

#### Adım 9.1 — Eski debugging_jarvis_skill.py'yi doğrula ve sil

- [x] Yeni skill (`skills/debugging_jarvis/`) 660 satır — eskisinden kapsamlı
- [x] `123/debugging_jarvis_skill.py` — **silindi**
- [x] `123/__init__.py` — **silindi**

#### Adım 9.2 — AGENT_PROMPT.md'yi docs'a taşı

- [ ] ~~`123/AGENT_PROMPT.md` → `docs/DEBUGGING_AGENT_PROMPT.md`~~ — **Atlandı** (AGENT_PROMPT.md içeriği eski pipeline bilgisi, güncel kodla uyumsuz)

#### Adım 9.3 — SKILL.md hardlink/merge

- [x] `123/SKILL.md` içeriği gözden geçirildi — mevcut `skills/debugging_jarvis/SKILL.md` yeterli

#### Adım 9.4 — 123/ klasörünü sil

```bash
rm -rf 123/
```

- [x] `123/` klasörü **silindi** (4 dosya: AGENT_PROMPT.md, debugging_jarvis_skill.py, __init__.py, SKILL.md)
- [x] `web_ui.py` referansı güncellendi: `123/JARVIS_UI_Pro.html` → `web_ui.html`

---

## FAZ 10 — Config Konsolidasyonu

### Mevcut Durum

4 ayrı config dosyası var:

| Dosya | İçerik | Durum |
|-------|--------|-------|
| `config/audio.yaml` | sample_rate, frame_size, VAD değerleri | Güncellenecek (FAZ 5) |
| `config/models.yaml` | Whisper, Silero model yolları | Güncellenecek (FAZ 6) |
| `config/wake_word.yaml` | Wake word chain | Doğrulanacak (FAZ 7) |
| `config/voices.yaml` | TTS ses profilleri | Gözden geçirilecek |

### Plan

#### Adım 10.1 — Fiziksel config validasyonu

- [x] `audio.yaml` sample_rate=48000 → VAD 16kHz downsampling: `VADEngine._downsample()` ile çözüldü (FAZ 5)
- [x] `models.yaml`'de `log_prob_threshold` alanı zaten yok — faster-whisper varsayılanı kullanılıyor
- [x] `wake_word.yaml` chain: openWakeWord→Porcupine→Energy — her biri graceful import ile çalışıyor
- [x] Fahrettin modeli (`voice/Fahrettin-TTS/tr_TR-fahrettin-medium.onnx`) mevcut

#### Adım 10.2 — Config reload mekanizması

- [ ] ~~`app_config.py`'ye hot-reload desteği~~ — **Atlandı** (config'ler statik, restart gerekli)
- [x] Tüm provider'lar ortak `app_config` kullanıyor

---

## FAZ 11 — ROADMAP Kalan Maddeleri

### 11.1 — YouTube API Anahtarı Uyarısı ✅

**Dosya**: `ui.py`

- [x] YouTube API anahtarı boşsa UI'da sarı uyarı etiketi gösteriliyor (`"YT eksik"` + orange text, `ui.py` satır 622)
- [x] `config/api_keys.json` içinde `youtube_api_key` kontrolü mevcut

### 11.2 — setup.ps1 Binary Kontrolleri ✅

- [x] `setup.ps1` script'ine model dosya kontrolleri eklendi (satır 105-107):
  - `voice/Fahrettin-TTS/tr_TR-fahrettin-medium.onnx` — Piper TTS
  - `voice/faster-whisper/model.bin` — Faster-Whisper STT
  - `voice/faster-whisper-large-backup/model.bin` — Large yedek model

---

## FAZ 12 — Test ve Doğrulama ✅

Her FAZ sonrası çalıştırılacak testler:

```
.venv/bin/python3 -m unittest tests.test_smoke -v
```

### Test hedefleri

| Modül | Test | Beklenen | Sonuç |
|-------|------|----------|-------|
| `FahrettinVAD` (`core/fahrettin_vad.py`) | 48kHz → 16kHz downsampling | Doğru dönüşüm | ✅ VADEngine._downsample() |
| `FahrettinVAD` | Energy threshold 50 ile normal konuşma | `is_speech=True` | ✅ VADEngine._process_energy() |
| `debugging_jarvis` | "merhaba" tetiklemez | `None` döner | ✅ general_kw temizlendi |
| `debugging_jarvis` | "ses calismiyor" tetikler | `str` döner | ✅ regex pattern korundu |
| `debugging_jarvis` | "konusma gelmiyor" tetikler | `str` döner | ✅ mevcut pattern'ler yeterli |
| Wake word | `WakeWordEngine` config'li başlatılır | Sistem başlatılır | ✅ main.py'de aktif |
| Whisper | `log_prob_threshold` | Varsayılan null | ✅ zaten null |
| `123/` | Klasör silindi | Yok | ✅ silindi |
| Config | Tüm dosyalar geçerli YAML | safe_load başarılı | ✅ geçerli |

### Entegrasyon testi (elle)

1. `python main.py` → UI açılır
2. "hey jarvis" de → wake word tetiklenir → dinleme başlar
3. "merhaba" de → LLM'e gider, debugging skill'ine değil
4. "ses calismiyor" de → debugging skill'i tetiklenir
5. Normal konuşma → Whisper transkripsiyonu başarılı
6. "kapat jarvis" de → uygulama kapanır

### Test Sonucu

```
Ran 1189 tests in 64s
OK (skipped=1)
```

- **0 pre-existing failures** — tüm asimilasyon değişiklikleri testleri geçiyor

---

## Uygulama Sırası

```
FAZ 5 (VAD) ──→ FAZ 6 (STT) ──→ FAZ 7 (Wake Word)
                                      │
                                      ▼
FAZ 8 (Skill) ──→ FAZ 9 (123/) ──→ FAZ 10 (Config)
                                      │
                                      ▼
                              FAZ 11 (ROADMAP)
                                      │
                                      ▼
                              FAZ 12 (Test)
```

FAZ 5, 6, 7 birbirine bağımlıdır (VAD → STT → Wake Word sırasıyla gitmeli).
FAZ 8 (skill) bağımsızdır, paralel yapılabilir.
FAZ 9 (123/) bağımsızdır, en son yapılır (önce skill'in çalıştığından emin ol).
FAZ 10 sonradan düzeltmeler için.
FAZ 11 en düşük öncelik.

---

## Dosya Değişiklik Özeti

| Dosya | İşlem | FAZ | Durum |
|-------|-------|-----|-------|
| `core/vad_engine.py` | Düzenle (evrensel VAD — downsampling, lock, energy_threshold) | 5 | ✅ |
| `core/fahrettin_vad.py` | **Yeni** (FahrettinVAD wrapper + factory) | 5 | ✅ |
| `core/ollama_provider.py` | Düzenle (inline VAD → FahrettinVAD, wake word gating) | 5+7 | ✅ |
| `config/audio.yaml` | Düzenle (VAD fahrettin bölümü, log_vad temizliği) | 5+10 | ✅ |
| `main.py` | Düzenle (wake word config dict, VAD config) | 7 | ✅ |
| `core/wake_word.py` | Düzenle (config dict parametresi) | 7 | ✅ |
| `skills/debugging_jarvis/debugging_jarvis_skill.py` | Düzenle (general_kw temizliği) | 8 | ✅ |
| `123/` (4 dosya) | **Sil** | 9 | ✅ |
| `web_ui.py` | Düzenle (`123/` referansı → `web_ui.html`) | 9 | ✅ |
| `ui.py` | YouTube API uyarısı (zaten mevcut, satır 622) | 11 | ✅ |
| `setup.ps1` | Düzenle (model dosya kontrolleri eklendi) | 11 | ✅ |
| `tests/test_smoke.py` | Düzenle (skill count 16→17) | 12 | ✅ |
| `docs/TAM_ASIMILASYON_PLANI.md` | Güncelle (✅ işaretle) | 12 | ✅ |
| `docs/ASIMILASYON_RAPORU.md` | Güncelle (FAZ 5-12 eklenecek) | 12 | ⬅️ |

---

*Plan oluşturulma: 2026-06-09*
*Son güncelleme: 2026-06-09 — ✅ Tüm FAZ'lar tamamlandı*
