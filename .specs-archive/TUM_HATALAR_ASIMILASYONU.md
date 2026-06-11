# J.A.R.V.I.S — Tüm Hata ve Eksiklerin Asimilasyon Planı

> **Kapsam**: LSP hataları, test başarısızlıkları, config/implementation uyumsuzlukları, dead code, cross-platform sorunları, eksik özellikler.
> **Tarih**: 2026-06-09
> **Durum**: ✅ Tamamlandı — A1–A8 uygulandı (A9 güncellendi, A10 opsiyonel)

---

## İçindekiler

1. [🔴 KRİTİK — LSP Derleme Hataları (6 adet)](#🔴-kritik--lsp-derleme-hataları-6-adet)
2. [🟠 YÜKSEK — Test Başarısızlıkları (3 adet)](#🟠-yüksek--test-başarısızlıkları-3-adet)
3. [🟡 ORTA — Cross-Platform & Entegrasyon](#🟡-orta--cross-platform--entegrasyon)
4. [🟢 DÜŞÜK — Kod Kalitesi & Refactor](#🟢-düşük--kod-kalitesi--refactor)
5. [⚪ OPSİYONEL — Yeni Özellikler & İyileştirmeler](#⚪-opsiyonel--yeni-özellikler--iyileştirmeler)
6. [Uygulama Sırası](#uygulama-sırası)

---

## 🔴 KRİTİK — LSP Derleme Hataları (6 adet)

Bunlar `basedpyright` LSP'nin rapor ettiği **gerçek tip hatası** içeren satırlar. Çalışma zamanında crash'e yol açabilir.

### K1 — `ollama_provider.py:462` — Geçersiz tip ifadesi

| Alan | Detay |
|------|-------|
| **Dosya** | `core/ollama_provider.py:462` |
| **Hata** | `reportInvalidTypeForm` — "Tür ifadesinde değişkene izin verilmiyor" |
| **Kod** | `self._fahrettin_vad: FahrettinVAD \| None = None` |
| **Kök neden** | `FahrettinVAD` module-level'da `try/except` ile tanımlı: import başarısızsa `FahrettinVAD = None` atanıyor. LSP, `None` değerinin tip olarak kullanılmasını reddediyor. |
| **Çözüm** | `from __future__ import annotations` zaten var (satır 7). Tip notasyonu string literal yap: `self._fahrettin_vad: "FahrettinVAD \| None" = None` |
| **Çaba** | 2 dk |

### K2 — `ollama_provider.py:468` — None çağrılabilir değil

| Alan | Detay |
|------|-------|
| **Dosya** | `core/ollama_provider.py:468` |
| **Hata** | `reportOptionalCall` — "None türündeki nesne çağrılamaz" |
| **Kod** | `self._fahrettin_vad = FahrettinVAD(config=audio_cfg, ...)` |
| **Kök neden** | Aynı sebep: `FahrettinVAD` import başarısızsa `None` olur. LSP `None(...)` çağrısını işaretler. |
| **Çözüm** | `_HAS_FAHRETTIN_VAD` flag'i zaten kontrol ediliyor (satır 463). LSP bunu anlamıyor. `assert FahrettinVAD is not None` ekle veya `typing.cast()` kullan. En temiz: `if _HAS_FAHRETTIN_VAD and FahrettinVAD is not None:` |
| **Çaba** | 2 dk |

### K3-K5 — `ollama_voice=` parametre hatası (3 dosya)

| Alan | Detay |
|------|-------|
| **Dosyalar** | `core/proactive_voice.py:144`, `core/streaming_tts.py:218`, `core/thinking_aloud.py:127` |
| **Hata** | `reportCallIssue` — "ollama_voice adlı parametre yok" |
| **Kod** | `speak_text(message, ollama_voice=self.voice)` |
| **Kök neden** | `actions/tts.speak_text()` fonksiyon imzası: `speak_text(text, voice=None, blocking=False)` — `ollama_voice` parametresi yok. Eski bir API'den kalma. |
| **Çözüm** | 3 dosyada `ollama_voice=self.voice` → `voice=self.voice` olarak değiştir. Ya da `actions/tts.py`'deki `speak_text` fonksiyonuna `**kwargs` ekle (kötü çözüm). |
| **Çaba** | 5 dk |

### K6 — `tts_engine.py:254` — `dict.get()` tip uyuşmazlığı

| Alan | Detay |
|------|-------|
| **Dosya** | `core/audio_system/tts_engine.py:254` |
| **Hata** | `reportCallIssue` — "get için aşırı yüklemelerin hiçbiri sağlanan bağımsız değişkenlerle eşleşmiyor" |
| **Kod** | `voice_id = self._voice_map.get(voice, "tr-TR-AhmetNeural")` |
| **Kök neden** | `voice: Optional[str] = None`, `_voice_map: dict[str, str]`. `dict[str, str].get()` `str` anahtar bekler ama `str \| None` alıyor. |
| **Çözüm** | `voice_id = self._voice_map.get(voice or "tr-TR-AhmetNeural")` veya tipi `voice: str = "tr-TR-AhmetNeural"` yap. |
| **Çaba** | 2 dk |

---

## 🟠 YÜKSEK — Test Başarısızlıkları (3 adet)

### T1 — `test_edge_voice_name` — `_edge_voice_name` fonksiyonu yok

| Alan | Detay |
|------|-------|
| **Dosya** | `tests/test_smoke.py:693` → `actions/tts.py` |
| **Hata** | `AttributeError: module 'actions.tts' has no attribute '_edge_voice_name'` |
| **Kök neden** | `actions/tts.py` sadece 12 satır, `core/audio_system/tts_engine.py`'den `speak_text` ve `get_tts_engine` re-export ediyor. `_edge_voice_name` fonksiyonu **hiçbir yerde yok**. Eski bir Edge TTS implementasyonundan kalma test. |
| **Çözüm** | **Seçenek A**: `actions/tts.py`'ye `_edge_voice_name()` fonksiyonunu ekle (edge ses adlarını maple). **Seçenek B**: Testi güncelle (mevcut API'ye uygun hale getir). **Öneri**: A — çünkü UI ses seçimi için gerekli. |
| **Çaba** | 15 dk |

### T2 — `test_tts_module_has_expected_functions` — `get_available_voices` yok

| Alan | Detay |
|------|-------|
| **Dosya** | `tests/test_smoke.py:219` → `actions/tts.py` |
| **Hata** | `AssertionError: Eksik: get_available_voices` |
| **Kök neden** | `actions/tts.py` `get_available_voices` fonksiyonunu export etmiyor. `core/audio_system/tts_engine.py`'de de böyle bir fonksiyon yok. |
| **Çözüm** | `actions/tts.py`'ye `get_available_voices()` ekle: `core/audio_system/tts_engine`'deki tüm engine'leri tara, her birinin `name` property'sini ve `is_available()` durumunu döndür. |
| **Çaba** | 20 dk |

### T3 — `test_no_log_files_in_root` — `jarvis_debug.log`

| Alan | Detay |
|------|-------|
| **Dosya** | `tests/test_smoke.py:55` → `/jarvis_debug.log` |
| **Hata** | `AssertionError: Kokte log: [PosixPath('/.../jarvis_debug.log')]` |
| **Kök neden** | `jarvis_debug.log` (77KB) proje kökünde duruyor. `main.py` çalışınca veya test'ler sırasında oluşuyor. |
| **Çözüm** | Log dosyasını `logs/` dizinine taşı veya `.gitignore`'a ekle (zaten `*.log` var ama dosya önceden oluşmuş). En temizi: loglama konfigürasyonunu `logs/` dizinine yönlendir. |
| **Çaba** | 5 dk |

---

## 🟡 ORTA — Cross-Platform & Entegrasyon

### C1 — VAD double downsampling

| Alan | Detay |
|------|-------|
| **Dosyalar** | `core/vad_engine.py:135` (`_downsample`), `core/ollama_provider.py:510-514` (`scipy.signal.resample`) |
| **Sorun** | OllamaProvider'ın STT döngüsü önce kendi `scipy.signal.resample()` ile 48→16kHz dönüşümü yapıyor, SONRA `FahrettinVAD.is_speech()` çağrılıyor. FahrettinVAD da `VADEngine.process_frame()` içinde tekrar `_downsample()` yapıyor. **Gereksiz çift dönüşüm.** |
| **Çözüm** | OllamaProvider STT döngüsündeki `scipy.signal.resample()` kaldırılmalı. VAD engine kendi downsampling'ini zaten yapıyor. Ancak STT (Whisper) de 16kHz bekliyor — resample sonrası `data` değişkeni hem VAD'a hem STT'ye gidiyor. Ya VAD'a ham data ver (engine downsampler ile), ya da STT'ye resample edilmiş data ver. **Öneri**: VAD'a `sample_rate=48000` ile ham data gönder (engine downsampler yapar), STT için ise mevcut resample'ı koru. Yani VAD çağrısını `resample` öncesine taşı. |
| **Çaba** | 15 dk |

### C2 — `actions/tts.py` yeniden yapılandırma

| Alan | Detay |
|------|-------|
| **Dosya** | `actions/tts.py` (12 satır) |
| **Sorun** | Sadece re-export yapıyor. Oysa testler `get_available_voices()` ve `_edge_voice_name()` bekliyor. Ayrıca 3 dosya `ollama_voice=` parametresiyle çağrı yapıyor (K3-K5). |
| **Çözüm** | `actions/tts.py`'yi gerçek bir arayüz katmanına dönüştür: `get_available_voices()` (engine'leri tara + is_available kontrolü), `_edge_voice_name()` (edge ses adı→ID dönüşümü), `speak_text()` (mevcut). |
| **Çaba** | 30 dk |

### C3 — Windows-specific kod Linux'ta import hatası

| Alan | Detay |
|------|-------|
| **Dosya** | `actions/windows_utils.py:3-4` — `import ctypes, ctypes.wintypes` |
| **Sorun** | `ctypes.wintypes` sadece Windows'ta var. Linux'ta `ImportError` fırlatır. Modülün altında platform kontrolleri var mı bilinmiyor. |
| **Çözüm** | `try/except ImportError` ile sar veya `platform.system()` kontrolü ekle. |
| **Çaba** | 10 dk |

### C4 — OllamaProvider+GeminiProvider VAD instance duality

| Alan | Detay |
|------|-------|
| **Dosyalar** | `main.py:280` (VADEngine), `core/ollama_provider.py:468` (FahrettinVAD) |
| **Sorun** | İki ayrı VAD instance'ı çalışıyor: `main.py`'deki `VADEngine` UI state callbacks için, `ollama_provider.py`'deki `FahrettinVAD` STT VAD için. Aynı threshold'ları kullanmıyor olabilirler. |
| **Çözüm** | İkinci aşama optimizasyon. Şimdilik düzeltme gerektirmiyor (çalışıyor). Not olarak ekle. |
| **Çaba** | — |

### C5 — `_user_initiated` gate + wake word interaction

| Alan | Detay |
|------|-------|
| **Dosyalar** | `main.py` (`_user_initiated`), `core/ollama_provider.py:546-553` (`_is_awake`) |
| **Sorun** | Wake word (`_is_awake`) ile `_user_initiated` gate arasındaki etkileşim tanımlı değil. Wake word ile gelen komutlar AI tool'ları çağırabilir mi? |
| **Çözüm** | Wake word tetiklendiğinde `_user_initiated = True` yapılmalı (zaten `ollama_provider.py:602`'de yapılıyor — `j._user_initiated = True`). Doğrula. |
| **Çaba** | 5 dk (doğrulama) |

---

## 🟢 DÜŞÜK — Kod Kalitesi & Refactor

### Q1 — `ui.py` refactor (1905 satır)

| Alan | Detay |
|------|-------|
| **Dosya** | `ui.py` |
| **Sorun** | 1905 satırlık monolitik Tkinter UI. `ui/` paketi var ama `ui.py` hala ana dosya olarak kullanılıyor. Method'ları `ui/` altındaki modüllere taşımak gerek. |
| **Çözüm** | Adım adım: `JarvisUI.setup_ui()` parçalanabilir (widget factory'ler), state management ayrılabilir, event handlers ayrılabilir. |
| **Çaba** | 2-4 saat |

### Q2 — `test_smoke.py` çok büyüdü (2084 satır)

| Alan | Detay |
|------|-------|
| **Dosya** | `tests/test_smoke.py` |
| **Sorun** | Tüm testler tek dosyada. 2084 satır, navigasyon zor. |
| **Çözüm** | Her modül için ayrı test dosyası: `test_core.py`, `test_actions.py`, `test_skills.py`, `test_ui.py` |
| **Çaba** | 1 saat |

### Q3 — `from __future__ import annotations` eksik

| Dosya | Durum |
|-------|-------|
| `core/ollama_provider.py` | ✅ Var (satır 7) |
| `core/vad_engine.py` | ✅ Var (satır 6) |
| `actions/tts.py` | ✅ Var (satır 6) |
| `actions/windows_utils.py` | ✅ Var (satır 1) |
| Diğer 30+ dosya | ⚠️ Çoğunda yok |
| **Çözüm** | Tüm `.py` dosyalarına `from __future__ import annotations` ekle (modern Python pratiği, tip kontrolünü iyileştirir). |
| **Çaba** | 15 dk (bulk edit) |

### Q4 — `# type: ignore` suppressions

| Dosya | Satır | Açıklama |
|-------|-------|----------|
| `core/ollama_provider.py` | 29, 37 | `FahrettinVAD = None # type: ignore`, `NoiseSuppressor = None # type: ignore` |
| **Çözüm** | `# type: ignore` yerine `None` atamasını `typing.cast()` veya `Optional[Type]` ile yap. |
| **Çaba** | 10 dk |

### Q5 — Debug `print()`'ler üretim kodunda

| Dosya | Satır(lar) | İçerik |
|-------|-----------|--------|
| `core/ollama_provider.py` | 474, 477, 481, 488, 494, 504, 506, 530, 543 | `print("[Ollama STT DEBUG] ...")` |
| **Sorun** | Debug amaçlı print'ler üretimde gereksiz console kirliliği. |
| **Çözüm** | `write_log()` veya `logging.debug()` kullan. Ya da `_DEBUG` flag'i ile kontrol et. |
| **Çaba** | 10 dk |

### Q6 — Tutarsız import stili

| Dosya(lar) | Sorun |
|-----------|-------|
| Bazı dosyalar `from x import y`, bazıları `import x.y` | Proje standardı `from x import y` (CLAUDE.md'de belirtilmemiş) |
| **Çözüm** | Kod review + standartlaştırma. Düşük öncelik. |
| **Çaba** | 20 dk |

---

## ⚪ OPSİYONEL — Yeni Özellikler & İyileştirmeler

### F1 — `playsound` → `simpleaudio` geçişi

| Alan | Detay |
|------|-------|
| **ROADMAP** | Belirtilmiş: "playsound artık bakımda değil" |
| **Çözüm** | `playsound` kullanımını bul → `simpleaudio` veya `pygame` ile değiştir. |
| **Çaba** | 30 dk |

### F2 — Birim testleri (action modülleri için)

| Alan | Detay |
|------|-------|
| **ROADMAP** | Orta vade: "Her action modülü için unittest" |
| **Şu an** | Sadece smoke test (import + temel API kontrolü). Pure fonksiyonlar için unit test yok. |
| **Çaba** | 4-8 saat |

### F3 — Type hint eksikleri

| Alan | Detay |
|------|-------|
| **ROADMAP** | Orta vade: "Tüm public fonksiyonlara tam tip eklenmeli" |
| **Çözüm** | LSP'nin bulduğu tüm `reportUnknownParameterType`, `reportMissingTypeArgument` vb. uyarıları temizle. |
| **Çaba** | 2-3 saat |

### F4 — Log viewer (UI'da)

| Alan | Detay |
|------|-------|
| **ROADMAP** | Orta vade |
| **Çaba** | 2 saat |

### F5 — Mikrofon seviye göstergesi (UI'da)

| Alan | Detay |
|------|-------|
| **ROADMAP** | Orta vade: FahrettinVAD `get_debug_stats()`'den RMS alınabilir |
| **Çaba** | 1 saat |

### F6 — Ses akışı watchdog

| Alan | Detay |
|------|-------|
| **ROADMAP** | Orta vade: "Kesinti tespiti + otomatik yeniden bağlanma" |
| **Çaba** | 2 saat |

### F7 — Çoklu kullanıcı profili

| Alan | Detay |
|------|-------|
| **ROADMAP** | Orta vade |
| **Çaba** | 4+ saat |

### F8 — UI scaling / pencere boyutu

| Alan | Detay |
|------|-------|
| **ROADMAP** | Bilinen sınırlama: 2200×1320 sabit |
| **Çaba** | 2 saat |

---

## Uygulama Sırası

```
FAZ K1-K6 (LSP) ──→ FAZ T1-T3 (Test) ──→ FAZ C1-C5 (Entegrasyon)
       │                    │                       │
       ▼                    ▼                       ▼
  5 dk toplam          40 dk toplam            60 dk toplam
                                                    │
                                                    ▼
                                          FAZ Q1-Q6 (Kalite)
                                                    │
                                                    ▼
                                              2-4 saat toplam
                                                    │
                                                    ▼
                                          FAZ F1-F8 (Opsiyonel)
                                                    │
                                                    ▼
                                              8-20 saat toplam
```

| Aşama | İş | Süre | Bağımlılık |
|-------|-----|------|-----------|
| **A1** | 🔴 K1-K6 — LSP hataları | ~10 dk | Yok |
| **A2** | 🟠 T1-T3 + C2 — TTS modülü yeniden yapılandırma | ~40 dk | A1 (K3-K5 ile aynı dosya) |
| **A3** | 🟡 C1 — VAD double downsampling fix | ~15 dk | A1 |
| **A4** | 🟡 C3 — Windows-import koruması | ~10 dk | Yok |
| **A5** | 🟡 C5 — Wake word + user_initiated doğrulama | ~5 dk | Yok |
| **A6** | 🟢 Q4 — `# type: ignore` temizliği | ~10 dk | A1 |
| **A7** | 🟢 Q5 — Debug print'leri temizle | ~10 dk | Yok |
| **A8** | 🟢 Q3 — `from __future__ import annotations` bulk | ~15 dk | Yok |
| **A9** | Analiz: ROADMAP.md güncelleme (eskileri ✅, yenilerini ekle) | ~15 dk | A1-A8 |
| **A10** | 🟢 Q1-Q2 — ui.py + test_smoke.py refactor (opsiyonel) | ~3-5 saat | A9 |
| **A11** | ⚪ F1-F8 — Opsiyonel özellikler | ~8-20 saat | A10 |

---

## Özet

| Kategori | Adet | Süre | Öncelik |
|----------|------|------|---------|
| 🔴 KRİTİK (LSP hataları) | 6 | ~10 dk | **EN ÖNCE** |
| 🟠 YÜKSEK (Test failures) | 3 | ~40 dk | Hemen |
| 🟡 ORTA (Cross-platform) | 5 | ~45 dk | Sonra |
| 🟢 DÜŞÜK (Kalite) | 6 | ~45 dk | Ara sıra |
| ⚪ OPSİYONEL (Yeni özellik) | 8 | ~8-20 saat | Planlanmamış |
| **Toplam (zorunlu)** | **20** | **~2-3 saat** | |

---

*Plan oluşturulma: 2026-06-09*
*Kapsam: LSP diagnostics, test failures, kod incelemesi, ROADMAP analizi*
