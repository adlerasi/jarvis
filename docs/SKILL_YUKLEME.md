# JARVIS Skill Sistemi — Detaylı Yükleme ve Geliştirme Kılavuzu

## İçindekiler

1. [Skill Nedir?](#skill-nedir)
2. [Dizin Yapısı](#dizin-yapısı)
3. [Skill Oluşturma Adım Adım](#skill-oluşturma-adım-adım)
4. [TRIGGERS Pattern'leri](#triggers-patternleri)
5. [Türkçe ASCII Fallback Kuralı](#türkçe-ascii-fallback-kuralı)
6. [Skill Metadata (SKILL_ID, SKILL_NAME, SKILL_VERSION)](#skill-metadata)
7. [SkillManager v3 — Hot-Reload](#skillmanager-v3--hot-reload)
8. [Mevcut Skill'ler (15 Adet)](#mevcut-skilller-15-adet)
9. [Action Modülü vs Skill Farkı](#action-modülü-vs-skill-farkı)
10. [Skill Test Etme](#skill-test-etme)
11. [Sık Yapılan Hatalar](#sık-yapılan-hatalar)
12. [En İyi Uygulamalar](#en-iyi-uygulamalar)

---

## Skill Nedir?

Skill, kullanıcının sesli/metin komutunu **AI'a göndermeden önce** yakalayan, doğrudan işleyen bir modüldür. AI düşünme süresini (~1-3sn) tamamen atlar, milisaniyeler içinde yanıt verir.

### Ne Zaman Skill Kullanılır?

| Durum | Skill mi? | AI mı? |
|-------|-----------|--------|
| "youtube aç" | ✅ Skill (öngörülebilir) | ❌ |
| "bugün hava nasıl" | ✅ Skill (öngörülebilir) | ❌ |
| "chrome'u kapat" | ✅ Skill (öngörülebilir) | ❌ |
| "merhaba nasılsın" | ❌ | ✅ AI (sohbet) |
| "bana bir şiir yaz" | ❌ | ✅ AI (yaratıcı) |

---

## Dizin Yapısı

```
skills/
├── <skill_adi>/                    # Her skill kendi klasöründe
│   ├── <skill_adi>_skill.py        # Ana mantık (ZORUNLU)
│   └── SKILL.md                    # Tanıtım dosyası (OPSİYONEL)
├── browser/
│   ├── browser_skill.py            # route_browser_request()
│   └── SKILL.md
├── weather/
│   ├── weather_skill.py            # route_weather_request()
│   └── SKILL.md
├── demo/                           # Hot-reload test skill'i
│   └── demo_skill.py               # route_demo_request()
└── ...
```

**Kurallar:**
- Klasör adı ile `.py` dosya adı **aynı** olmalı: `weather/` → `weather_skill.py`
- Route fonksiyonu **`route_<klasor_adi>_request`** formatında olmalı: `route_weather_request`
- SkillManager tüm skill'leri **otomatik keşfeder**, kayıt gerekmez

---

## Skill Oluşturma Adım Adım

### Adım 1: Klasör ve Dosya Oluştur

```bash
mkdir -p skills/yeni_skill
touch skills/yeni_skill/yeni_skill.py
```

### Adım 2: İskelet Kodu Yaz

```python
"""
Yeni Skill — Ne işe yaradığını açıkla.
"""

from __future__ import annotations
import re

# ── Metadata (opsiyonel ama önerilir) ──────────────────────────
SKILL_ID = "yeni-skill-v1"       # Benzersiz ID
SKILL_NAME = "Yeni Skill"        # Gösterim adı
SKILL_VERSION = "1.0.0"          # Versiyon

# ── Trigger patterns ──────────────────────────────────────────
# ASCII fallback: ş→s, ç→c, ü→u, ö→o, ğ→g, ı→i
TRIGGERS = {
    "action_bir": [
        r"(?:tetikleyici).*?(?:kelime)",
    ],
    "action_iki": [
        r"(?:ornek|örnek).*?(?:calistir|çalıştır)",
    ],
}


def classify_intent(text: str) -> tuple[str, dict]:
    """Kullanıcı metninden intent çıkar."""
    text_lower = text.lower().strip()

    # Intent 1
    for pattern in TRIGGERS["action_bir"]:
        if re.search(pattern, text_lower):
            return "action_bir", {"param": "deger"}

    # Intent 2
    for pattern in TRIGGERS["action_iki"]:
        if re.search(pattern, text_lower):
            return "action_iki", {}

    # Fallback keyword
    keywords = ["anahtar", "kelime"]
    if any(kw in text_lower for kw in keywords):
        return "action_bir", {}

    return "none", {}


def execute_skill(action: str, params: dict) -> str:
    """Skill çalıştırıcı."""
    if action == "action_bir":
        return f"Action bir çalıştı: {params}"
    elif action == "action_iki":
        return "Action iki çalıştı"
    return f"Bilinmeyen action: {action}"


def route_yeni_skill_request(user_text: str) -> str | None:
    """Ana router — SkillManager bu fonksiyonu çağırır."""
    intent, params = classify_intent(user_text)
    if intent == "none":
        return None  # Eşleşmedi → LLM'e git
    return execute_skill(intent, params)
```

### Adım 3: Çalıştır

```bash
python main.py
```

Konsolda:
```
[SkillManager] ✓ yeni_skill skill yüklendi (v1.0.0)
```

---

## TRIGGERS Pattern'leri

Her intent için bir veya daha fazla regex pattern'i tanımlanır. SkillManager pattern'leri sırayla dener, **ilk eşleşen** kazanır.

### Pattern Yazma Kuralları

```python
TRIGGERS = {
    "intent_adi": [
        # 1. Ana pattern (en spesifik)
        r"(?:spesifik).*?(?:kelime|ifade)",
        # 2. Alternatif pattern (daha geniş)
        r"(?:genel).*?(?:anlam|durum)",
        # 3. Çok kısa komut
        r"^tek_kelime$",
    ],
}
```

### Özel Noktalar

| Konu | Açıklama | Örnek |
|------|----------|-------|
| **Sıralama önemli** | Spesifik → genel sırası | Önce "hata mesajı oku", sonra "ekranı oku" |
| **Case insensitive** | `text_lower()` ile zaten küçültülmüş | Pattern'de `[A-Z]` kullanma |
| **^ ve $ kullan** | Kesin eşleşme için | `r"^merhaba$"` sadece "merhaba" |
| **Non-capturing groups** | `(?:...)` kullan, `(...)` kullanma | `(?:ac|aç)` değil `(ac|aç)` |
| **Boşluk yönetimi** | `.*?` ile esnek ara | `r"(?:hava).*?(?:durum)"` |

---

## Türkçe ASCII Fallback Kuralı

**ZORUNLU**: Tüm Türkçe karakterler için ASCII alternatifi **aynı pattern içinde** belirtilmelidir.

### Doğru:
```python
r"(?:yavaş|yavas)"
r"(?:göster|goster)"
r"(?:işlem|islem)"
r"(?:çalıştır|calistir|calıs"
r"(?:ağ|ag|bağlantı|baglanti)"
```

### Yanlış:
```python
r"(?:yavaş)"             # "yavas" yazarsa eşleşmez
r"(?:göster)"            # "goster" yazarsa eşleşmez
r"(?:bağlantı)"          # "baglanti" yazarsa eşleşmez
```

### ASCII Fallback Tablosu

| Türkçe | ASCII |
|--------|-------|
| ş | s |
| ç | c |
| ü | u |
| ö | o |
| ğ | g |
| ı | i |

### Fallback Keyword'lerde de Aynı Kural

```python
weather_keywords = ["hava", "derece", "sıcaklık", "sicaklik", "yağmur", "yagmur"]
```

---

## Skill Metadata

### SKILL_ID

Benzersiz tanımlayıcı. `list_skills()` bu ID'yi döndürür.
Yoksa veya boşsa → klasör adı kullanılır.
Format: `<isim>-v<versiyon>` (örn: `weather-v1`, `calendar-v1`)

### SKILL_NAME

İnsan tarafından okunabilir isim. UI'da gösterim için.
Yoksa → klasör adı kullanılır.

### SKILL_VERSION

Versiyon numarası. Hot-reload takibi ve debug için.
Yoksa → `"0.0.0"`

### Örnek

```python
SKILL_ID = "weather-v1"        # → list_skills() "weather-v1" döner
SKILL_NAME = "Hava Durumu"     # → UI'da "Hava Durumu" görünür
SKILL_VERSION = "1.0.0"        # → "v1.0.0" olarak log'lanır
```

---

## SkillManager v3 — Hot-Reload

### Özellikler

| Özellik | Açıklama |
|---------|----------|
| **Auto-Reload** | 3 saniyede bir dosya değişikliği kontrolü |
| **Yeni Skill** | `skills/` klasörüne yeni klasör at → otomatik yüklenir |
| **Skill Güncelleme** | `.py` dosyasını kaydet → otomatik yeniden yüklenir |
| **Skill Kaldırma** | Klasörü sil → otomatik devre dışı kalır |
| **Callback Sistemi** | loaded/reloaded/disabled event'leri |
| **İstatistikler** | Başarı/basarsızlık/error sayısı |

### Manuel API

```python
sm = get_skill_manager()

# Skill yeniden yükle
sm.reload_skill("weather-v1")

# Tüm skill'leri yeniden yükle
sm.reload_all()

# Skill'i devre dışı bırak
sm.disable_skill("weather-v1")

# Skill'i aktif et
sm.enable_skill("weather-v1")

# Skill bilgisi
info = sm.get_skill_info("weather-v1")
print(info.version)       # "1.0.0"
print(info.load_count)    # kaç kez yüklendiği
print(info.error_count)   # hata sayısı

# İstatistikler
stats = sm.get_stats()
# {"total_skills": 15, "active": 15, "failed": 0, ...}

# Tüm skill'ler (detaylı)
for s in sm.list_all_skills():
    print(f"{s['skill_id']}: v{s['version']} - {'Aktif' if s['is_active'] else 'Devre disi'}")

# Callback ile reload event'lerini dinle
def on_event(event, skill_id):
    print(f"[SYS] {event}: {skill_id}")
sm.on_reload(on_event)

# Watcher'ı durdur
sm.stop_watcher()
```

### Watcher Davranışı

```python
# main.py'de varsayılan:
self.skill_manager = get_skill_manager()  # auto_reload=True, interval=3sn

# Watcher'ı kapatmak için:
self.skill_manager = get_skill_manager(auto_reload=False)

# Aralığı değiştirmek için:
self.skill_manager = get_skill_manager(reload_interval=5.0)
```

### Hot-Reload Testi

```bash
# Terminal 1: JARVIS çalışıyor
python main.py

# Terminal 2: Demo skill'ini düzenle
echo 'SKILL_VERSION = "2.0.0"' >> skills/demo/demo_skill.py
# Kaydet → 3sn sonra reload
```

---

## Mevcut Skill'ler (18 Adet)

| # | Skill | SKILL_ID | Klasör | Backend (actions/) |
|---|-------|----------|--------|-------------------|
| 1 | Ajan | `agent-v1` | `agent/` | tool_registry |
| 2 | Tarayıcı | `browser` | `browser/` | `browser` |
| 3 | Takvim | `calendar-v1` | `calendar/` | `calendar` |
| 4 | Debugging | `debugging-jarvis-v1` | `debugging_jarvis/` | — |
| 5 | Dosya Yöneticisi | `file-manager-v1` | `file_manager/` | `file_guardian` |
| 6 | Karşılama | `greeting-v1` | `greeting/` | — |
| 7 | Medya | `media-v1` | `media/` | `media` |
| 8 | Ağ İzleme | `network-v1` | `network/` | `network_monitor` |
| 9 | Süreç Kontrol | `process-control-v1` | `process_control/` | `process_manager` |
| 10 | Hatırlatıcı | `reminders-v1` | `reminders/` | `reminders` |
| 11 | Zamanlayıcı | `scheduler-v1` | `scheduler/` | `system_cron` |
| 12 | Servis Yönetimi | `services-v1` | `services/` | `service_monitor` |
| 13 | Sistem Sağlığı | `system-health-v1` | `system_health/` | `system_doctor` |
| 14 | Ekran Analizi | `vision-v1` | `vision/` | `screen_vision` |
| 15 | Sesle Kodlama | `voice-coding-v1` | `voice_coding/` | — |
| 16 | Hava Durumu | `weather-v1` | `weather/` | `weather` |
| 17 | WhatsApp | `whatsapp-v1` | `whatsapp/` | `whatsapp` |
| 18 | YouTube | `youtube-v1` | `youtube/` | `youtube_stats`, `media` |

### Routing Sırası

SkillManager router'ları **kayıt sırasına göre** (alfabetik klasör sırası) dener:

1. agent
2. browser
3. calendar
4. debugging_jarvis
5. file_manager
6. greeting
7. media
8. network
9. process_control
10. reminders
11. scheduler
12. services
13. system_health
14. vision
15. voice_coding
16. weather
17. whatsapp
18. youtube

---

## Action Modülü vs Skill Farkı

| | Action Modülü | Skill Modülü |
|---|---|---|
| **Kim çağırır?** | AI (function_call) | SkillManager, AI'dan önce |
| **AI dahil mi?** | Evet, AI düşünür sonra çağırır | Hayır, anında çalışır |
| **Hız** | ~1-3sn (AI düşünme süresi) | ~1ms |
| **Kayıt** | `TOOL_DECLARATIONS` + `_TOOL_HANDLERS` | `skills/` klasörü + `route_*_request()` |
| **Regex** | Yok (AI anlar) | Var (pattern eşleştirme) |
| **Kullanım** | Karmaşık, bağlam gerektiren işler | Basit, öngörülebilir komutlar |
| **Örnek** | "dünkü logları analiz et ve özet çıkar" | "chrome'u kapat" |

### İletişim Akışı

```
Kullanıcı: "chrome'u kapat"
         │
         ▼
   _on_text_command()
         │
         ├── SKILL: skill_manager.route(text)
         │       │
         │       ├── EŞLEŞTİ → skill doğrudan çalışır
         │       │              Sonuç UI'da gösterilir
         │       │              LLM'e GİDİLMEZ (hızlı!)
         │       │
         │       └── EŞLEŞMEDİ → LLM akışına devam
         │
         └── AI (Gemini/Ollama)
                 │
                 ├── Tool call → action modülü (yavaş)
                 └── Sohbet → direkt yanıt
```

---

## Skill Test Etme

### 1. Birim Test (test_smoke.py)

```python
def test_yeni_skill_import(self):
    """Yeni skill import edilebilmeli."""
    import importlib
    mod = importlib.import_module("skills.yeni_skill.yeni_skill")
    self.assertTrue(hasattr(mod, "route_yeni_skill_request"))
```

### 2. SkillManager Testi

```python
def test_yeni_skill_loaded(self):
    from core.skill_manager import get_skill_manager
    sm = get_skill_manager()
    skill_ids = sm.list_skills()
    self.assertIn("yeni-skill-v1", skill_ids)
```

### 3. Manuel Test (Python REPL)

```python
from core.skill_manager import get_skill_manager
sm = get_skill_manager()

# Test komutları
print(sm.route("yeni skill test"))    # Skill çalışıyor mu?
print(sm.route("merhaba"))            # None dönmeli (LLM'e gitmeli)

# İstatistikler
print(sm.get_stats())
```

### 4. Canlı Test

```bash
python main.py
# Konsolda: ✓ yeni_skill skill yüklendi (v1.0.0)
# Sonra: "yeni skill test" yaz → skill yanıtı görmelisin
```

---

## Sık Yapılan Hatalar

### 1. ASCII Fallback Unutuldu

```python
# ❌ YANLIŞ — "yavas" yazarsa çalışmaz
r"(?:yavaş)"
r"(?:göster)"

# ✅ DOĞRU
r"(?:yavaş|yavas)"
r"(?:göster|goster)"
```

### 2. Yanlış Route Fonksiyon Adı

SkillManager `route_<klasor>_request` arar. Klasör adı ile fonksiyon adı eşleşmeli:

```python
# ❌ YANLIŞ — klasör "yeni_skill" ama fonksiyon "route_new_skill_request"
def route_new_skill_request(user_text):

# ✅ DOĞRU
def route_yeni_skill_request(user_text):
```

### 3. Türkçe Karakter Regex'te ASCII Olmadan

```python
# ❌ YANLIŞ — regex engine ASCII'de farklı davranabilir
text_lower = user_text.lower()  # Bu zaten yapıldı mı?

# ✅ DOĞRU — kullanıcı metnini lowercase yap
text_lower = user_text.lower().strip()
```

### 4. Çok Geniş Pattern (False Positive)

```python
# ❌ YANLIŞ — "hava" geçen her şeyi yakalar
r"hava"

# ✅ DOĞRU — belirli bağlamda ara
r"(?:hava).*?(?:durum|nasıl|kaç derece|rapor)"
```

### 5. Intent Sırası Yanlış

```python
TRIGGERS = {
    "spesifik": [...],  # ÖNCE spesifik
    "genel": [...],     # SONRA genel
}
```

---

## En İyi Uygulamalar

1. **Spesifik pattern önce** — Geniş pattern'ler spesifik olanları ezmesin
2. **Fallback keyword** — Regex eşleşmezse keyword fallback ekle
3. **None dön** — Eşleşme yoksa `None` (AI'a bırak)
4. **Hata yakala** — `try/except` ile skill hatalarını yakala
5. **Tek sorumluluk** — Her skill tek bir işi yapsın
6. **ASCII fallback** — Her Türkçe karakter için ASCII alternatifi
7. **SKILL_ID ekle** — Hot-reload ve izleme için
8. **Thread-safe** — Skill fonksiyonları thread-safe olmalı
9. **Hızlı dön** — Skill 100ms'den hızlı yanıt vermeli
10. **Yan etki yok** — Skill sadece routing yapsın, aksiyonu action modülüne bırak

---

*Son güncelleme: 2026-06-07*
*Skill Manager v3 — Hot-Reload Destekli*
*15 skill — 228+ smoke test*
