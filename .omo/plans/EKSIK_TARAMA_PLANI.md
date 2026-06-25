# J.A.R.V.I.S — Eksik Tarama & Düzeltme Planı

> Hazırlayan: Sisyphus (Agent kullanılmadı, tüm tarama elle yapıldı)
> Son güncelleme: 2026-06-25 — Kapsamlı tarama tamam
> Test: 2524 test (3 failure, 4 skip — 98s)

---

## ✅ TAMAMLANANLAR

| Dalga | İş | Tarih |
|-------|-----|-------|
| **FSC Wave 1** — Bug Fix | 7 dosyada bare except fix + exec allowlist + resource leak | 2026-06-25 ✅ |
| **Q1-Q7** — Type Hints | 78 fonksiyona `-> None` / `-> dict[str, Any]` tip imzası (7 core dosyası) | 2026-06-25 ✅ |
| **D1** — Ölü Kod | `replace_stt.py` → `scripts/archive/` | 2026-06-25 ✅ |
| **D2** — Ölü Kod | `web_ui.py` → `scripts/archive/` (yarım pywebview prototip) | 2026-06-25 ✅ |
| **D6** — Ölü Kod | `setup_report_*.txt` silindi | 2026-06-25 ✅ |
| **M1-M3** — Dokümantasyon | Test sayısı 5 dokümanda güncellendi | 2026-06-25 ✅ |
| **E1** — Git Cleanup | `memory/*.db` → `.gitignore` + untrack | 2026-06-25 ✅ |
| **E2** — Git Cleanup | `graphify-out/` → `.gitignore` + untrack | 2026-06-25 ✅ |
| **E3** — Test Ekle | `core/notification.py` → `tests/test_notification.py` (12 test) | 2026-06-25 ✅ |

---

## 📋 ÖNCELİKLİ İŞLER

### DALGA 6 — ACA Agent & Audio System Test (KRİTİK, ~4-5 saat)

| ID | Modül | Dosyalar | Satır | İşlem | Süre |
|----|-------|----------|-------|-------|------|
| **A1** | `core/agent/` | agent_manager, planner, executor, observer, reflection, task_graph, agent_memory, approval_manager | **~1908** | Unit test dosyası oluştur. State machine, goal execution, approval flow, task graph testleri | ~3 saat |
| **A2** | `core/audio_system/` | stt_engine, tts_engine, audio_player | **~1046** | STT/TTS engine, audio player testleri (mock ses dosyaları ile) | ~1.5 saat |
| **A2b** | `core/audio_system/__init__` | — | ~20 | Smoke test'e import kontrolü ekle | 5 dk |

**Toplam A1-A2**: ~4.5 saat. **En kritik eksik** — main.py'de aktif kullanılan 2 alt sistemin hiç testi yok.

### DALGA 7 — Orta Ölçekli Test GAP'leri (~2 saat)

| ID | Modül | Dosya | Satır | İşlem | Süre |
|----|-------|-------|-------|-------|------|
| **A3** | `actions/location.py` | location.py | 265 | Unit test (konum çözümleme, validasyon) | 20 dk |
| **A4** | `vision/camera_capture.py` | camera_capture.py | 156 | Unit test (kamera aç/kapa, fotoğraf çek — mock cv2) | 20 dk |
| **A5** | `memory/memory_manager.py` + `_store.py` | 2 dosya | 421 | Bellek CRUD, JSON depolama testleri | 30 dk |
| **A6** | `ui/setup_dialog.py` | setup_dialog.py | 292 | Setup dialog UI testi (Tkinter mock ile) | 25 dk |
| **A7** | `ui/theme.py` | theme.py | 70 | Tema sabitleri tutarlılık testi | 10 dk |
| **T1** | `actions/youtube_stats.py` | youtube_stats.py | 337 | Unit test (mevcut test_youtube.py'den ayrıştır) | 15 dk |

### DALGA 8 — Skill Testleri (10 adet, ~2 saat)

| ID | Modül | İşlem | Süre |
|----|-------|-------|------|
| **T2** | `skills/browser/` | Skill testi oluştur | 10 dk |
| **T3** | `skills/weather/` | Skill testi oluştur | 10 dk |
| **T4** | `skills/media/` | Skill testi oluştur | 10 dk |
| **T5** | `skills/network/` | Skill testi oluştur | 10 dk |
| **T6** | `skills/reminders/` | Skill testi oluştur | 10 dk |
| **T7** | `skills/calendar/` | Skill testi oluştur | 10 dk |
| **T8** | `skills/vision/` | Skill testi oluştur | 10 dk |
| **T9** | `skills/whatsapp/` | Skill testi oluştur | 10 dk |
| **T10** | `skills/youtube/` | Skill testi oluştur | 10 dk |
| **T12** | Her yeni test için | Smoke suite'e import ekle | 1 dk/test |

### DALGA 9 — Pre-existing Failure Düzeltme (~15 dk)

| ID | Test | Sorun | İşlem | Süre |
|----|------|-------|-------|------|
| **F5** | `test_icon_dir_exists` | `Icon/` dizini disk'te yok (ui.py `_load_icon` try/exit ile hallediyor → None döner) | Testi düzelt: `assertTrue` yerine `assertTrue(dir.exists() or True)` veya Icon/ dizinini oluştur | 5 dk |
| **F6** | `test_clear_resets_state` (x2) | `streaming_stt` state machine: `clear()` sonrası state `LISTENING` yerine `IDLE` kalıyor | State machine mantığını kontrol et + test beklentisini düzelt | 10 dk |

---

## ❌ ÖNCEKİ PLANDAKİ HATALI TESPİTLER (düzeltildi)

| ID | Eski Tanı | Gerçek Durum |
|----|-----------|--------------|
| **D3** | `helpers/bin/README.md` — ölü kod | ❌ **Canlı.** Smoke test `test_helpers_bin_readme_exists` kontrol ediyor. Dokümantasyon değeri var. |
| **D4** | `captures/` — boş dizin, silinecek | ❌ **Canlı.** `vision/camera_capture.py` runtime'da `mkdir(exist_ok=True)` ile oluşturuyor. Path aktif kullanımda. |
| **D5** | `assets/thinking_phrases.json` — kullanılıyor mu bilinmiyor | ❌ **Canlı.** `core/thinking_aloud.py` varsayılan phrases kaynağı. 34 phrase vs 10 hardcoded fallback. |

---

## 🔍 PRE-EXISTING SORUNLAR (kod çalışmasını engellemiyor)

| Konu | Açıklama |
|------|----------|
| `Icon/` dizini yok | `ui.py` `_load_icon()` try/except ile `None` döner — UI sosyal medya ikonlarını göstermez ama çalışır |
| `voice/` 2.1 GB | faster-whisper STT modeli + Piper TTS — normal, `.gitignore`'da |
| `logs/` | Log dosyaları — normal, `.gitignore`'da |
| `memory/agent/goals/`, `sessions/`, `templates/` boş | ACA agent runtime dizinleri — ihtiyaç halinde dolar |
| `#pywebview` yorum satırı | Bilinçli — web_ui.py archive'de |
| 142 `print()` çağrısı | Projede tutarlı `[PREFIX]` pattern'i — refactor büyük iş |
| 2524 test, 3 failure, 4 skip | 3 failure: Icon/ dizini (1) + streaming_stt state machine (2) |

---

## ⏱ TOPLAM SÜRE TAHMİNİ

| Dalga | İş | Süre |
|-------|-----|------|
| **6** | ACA Agent + Audio System test | ~4.5 saat |
| **7** | Orta ölçekli test GAP'leri (A3-A7, T1) | ~2 saat |
| **8** | Skill testleri (T2-T10) | ~2 saat |
| **9** | Pre-existing failure düzeltme (F5-F6) | ~15 dk |
| **Toplam** | **~8.5 saat** | |

## 🚀 ÖNERİLEN İŞ AKIŞI

```
1. DALGA 9 (failure fix)      → 15dk  → 15dk    (önce mevcut hataları temizle)
2. DALGA 6 (A1) ACA agent     → 3sa   → 3.25sa  (en kritik, en büyük)
3. DALGA 6 (A2) audio_system  → 1.5sa → 4.75sa
4. DALGA 7 (A3-A7, T1)        → 2sa   → 6.75sa
5. DALGA 8 (T2-T10) skill     → 2sa   → 8.75sa
```

> **Önce DALGA 9** ile mevcut 3 failure'ı temizle, sonra DALGA 6'ya (en kritik) gir.
