# J.A.R.V.I.S — Skill Sistemi Dokumani

> Skill Manager v3 (Hot-Reload) — AI'siz dogrudan islem, aninda yanit.

---

## Nedir?

Skill sistemi, kullanici komutlarini **LLM'e gondermeden once** yakalayip dogrudan isleyen bir katmandir. Basit, ongorulebilir komutlar icin AI dusunme suresini (~1-3sn) ortadan kaldirarak aninda yanit verir.

**Ornek**: Kullanici "saat kac" dediginde skill dogrudan cevap verir, AI'a gitmez.

---

## Mimari

```
_on_text_command(user_text)
    |
    +-- 1. skill_manager.route(user_text) --> AI'SIZ, ANINDA
    |       |
    |       +-- ESLESTI --> skill sonucunu UI'da goster
    |       |              LLM'e GIDILMEZ
    |       |              Sure: ~1-10ms
    |       |
    |       +-- ESLESTMEDI --> None dondur
    |
    +-- 2. provider.send_text(user_text) --> NORMAL LLM AKISI
            AI dusunur, tool cagirir, yanit uretir
            Sure: ~1-5sn
```

---

## Skill Manager (`core/skill_manager.py`)

### Singleton, v3, Hot-Reload

```
SkillManager (__init__)
+-- 17 skill yukle (otomatik kesif)
+-- Watcher thread baslat (3sn interval)
|
+-- route(user_text) --> str | None
|   +-- Tum router fonksiyonlarini sirayla dene
|       +-- Ilk eslesen doner, digerleri atlanir
|
+-- list_skills() --> list[str] — yuklu skill'ler
+-- get_skill_info(name) --> SkillInfo | None
|
+-- reload_skill(name) --> bool
+-- disable_skill(name) --> bool
+-- enable_skill(name) --> bool
|
+-- on_loaded(fn) / on_reloaded(fn) / on_disabled(fn)
    +-- Callback kaydi
```

### SkillInfo Veri Yapisi

```python
@dataclass
class SkillInfo:
    skill_id: str            # "weather-v1"
    name: str                # "Weather"
    version: str             # "1.0"
    folder: str              # "weather"
    module_path: Path        # skills/weather/weather_skill.py
    md_path: Path | None     # skills/weather/SKILL.md
    route_func: Callable     # route_weather_request()
    loaded_at: datetime
    last_modified: float
    load_count: int
    error_count: int
    last_error: str | None
    is_active: bool
```

---

## Skill Dizin Yapisi

Her skill kendi klasorunde yasar:

```
skills/<name>/
+-- <name>_skill.py          # ZORUNLU — route fonksiyonu
+-- SKILL.md                 # OPSIYONEL — metadata (YAML frontmatter)
+-- triggers.json            # OPSIYONEL — trigger pattern'leri
```

### `<name>_skill.py` — Zorunlu Imza

```python
def route_<name>_request(user_text: str) -> str | None:
    """user_text'te trigger ara, eslesirse skill sonucunu dondur.
    Eslesmezse None dondur (LLM akisina devam).
    """
    ...
```

### SKILL.md — Opsiyonel Metadata

```yaml
---
SKILL_ID: weather-v1
SKILL_NAME: Weather
SKILL_VERSION: "1.0"
---
# Weather Skill

Hava durumu sorgulama ve ozet bilgi verme.
```

### Metadata Fallback

| Alan | SKILL.md varsa | Yoksa |
|------|---------------|-------|
| `SKILL_ID` | SKILL.md'deki deger | Klasor adi |
| `SKILL_NAME` | SKILL.md'deki deger | Klasor adi |
| `SKILL_VERSION` | SKILL.md'deki deger | "0.0.0" |

---

## Hot-Reload Mekanizmasi

```
Watcher Thread (3sn interval)
|
+-- skills/ klasorunu tara (os.listdir)
+-- Yeni klasor/dosya --> import et, route_func kaydet --> callback: loaded
+-- Degismis dosya (mtime) --> reload et --> callback: reloaded
+-- Silinmis dosya --> kaldir --> callback: disabled
+-- Hata --> error_count++ --> last_error kaydet
```

**Import Guvenligi**:
- `importlib.util.spec_from_file_location()` kullanilir
- Hatali import skill'i tek basina dusurur, tum sistemi etkilemez
- Hot-reload daemon thread'de calisir (graceful shutdown)

---

## Trigger Pattern'leri

Turkce karakterler icin **ASCII fallback ZORUNLUDUR**:

```python
# YANLIS — sadece Turkce karakter
TRIGGERS = {
    "slow_down": [r"yavasla"],
}

# DOGRU — ASCII fallback dahil
TRIGGERS = {
    "slow_down": [r"(?:yavasla|yavasla)"],
}
```

**Tum donusumler**:

| Karakter | Fallback | Ornek |
|----------|----------|-------|
| s | s | `(?:goster|goster)` |
| c | c | `(?:ac|ac)` |
| u | u | `(?:guncelle|guncelle)` |
| o | o | `(?:coz|coz)` |
| g | g | `(?:ag|ag)` |
| i | i | `(?:isi|isi)` |

---

## 18 Aktif Skill

### 1. agent-v1 (`skills/agent/`)
- **Dosya**: `agent_skill.py`
- **Tetikleyiciler**: "agent", "gorev", "senaryo", "planla"
- **Islev**: Otonom ajan gorev yonetimi

### 2. browser-v1 (`skills/browser/`)
- **Dosya**: `browser_skill.py`
- **Tetikleyiciler**: "browser ac", "internette ara", "github ac", "youtube"
- **Islev**: URL acma, Google arama, YouTube oynatma

### 3. calendar-v1 (`skills/calendar/`)
- **Dosya**: `calendar_skill.py`
- **Tetikleyiciler**: "takvim", "etkinlik", "randevu"
- **Islev**: Takvim okuma/ekleme/silme

### 4. debugging-jarvis-v1 (`skills/debugging_jarvis/`)
- **Dosya**: `debugging_jarvis_skill.py`
- **Tetikleyiciler**: "debug", "hata", "log", "sorun"
- **Islev**: JARVIS hata ayiklama ve durum bilgisi

### 5. file-manager-v1 (`skills/file_manager/`)
- **Dosya**: `file_manager_skill.py`
- **Tetikleyiciler**: "dosya", "klasor", "buyuk dosya", "mukerrer"
- **Islev**: Buyuk dosya bulma, yinelenen dosya tespiti, klasor temizlik

### 6. greeting-v1 (`skills/greeting/`)
- **Dosya**: `greeting_skill.py`
- **Tetikleyiciler**: "merhaba", "selam", "naber", "iyi gunler"
- **Islev**: Karsilama mesajlari

### 7. media-v1 (`skills/media/`)
- **Dosya**: `media_skill.py`
- **Tetikleyiciler**: "muzik", "sarki", "medya", "oynat"
- **Islev**: Medya oynatma (YouTube/Spotify/Apple Music)

### 8. network-v1 (`skills/network/`)
- **Dosya**: `network_skill.py`
- **Tetikleyiciler**: "ag", "network", "ping", "baglanti"
- **Islev**: Ag ozeti, baglanti listeleme, ping

### 9. process-control-v1 (`skills/process_control/`)
- **Dosya**: `process_control_skill.py`
- **Tetikleyiciler**: "gorev yoneticisi", "process", "surec"
- **Islev**: Surec listeleme/oldurme, port bulma

### 10. reminders-v1 (`skills/reminders/`)
- **Dosya**: `reminders_skill.py`
- **Tetikleyiciler**: "hatirlat", "reminder", "hatirlatma"
- **Islev**: Hatirlatici ekleme/listeleme

### 11. scheduler-v1 (`skills/scheduler/`)
- **Dosya**: `scheduler_skill.py`
- **Tetikleyiciler**: "zamanli", "gorev", "hatirlat", "cron"
- **Islev**: Zamanlanmis gorev ekleme/listeleme/silme

### 12. services-v1 (`skills/services/`)
- **Dosya**: `services_skill.py`
- **Tetikleyiciler**: "servis", "hizmet", "baslat", "durdur"
- **Islev**: Servis listeleme/baslatma/durdurma

### 13. system-health-v1 (`skills/system_health/`)
- **Dosya**: `system_health_skill.py`
- **Tetikleyiciler**: "sistem durumu", "sistem sagligi", "system health"
- **Islev**: CPU/RAM/Disk kullanim bilgisi

### 14. vision-v1 (`skills/vision/`)
- **Dosya**: `vision_skill.py`
- **Tetikleyiciler**: "ekran", "goruntu", "ne goruyorsun"
- **Islev**: Ekran goruntusu + Gemini Vision analizi

### 15. voice-coding-v1 (`skills/voice_coding/`)
- **Dosya**: `voice_coding_skill.py`
- **Tetikleyiciler**: "kod", "kodla", "yaz", "calistir"
- **Islev**: Sesle kod yazma ve calistirma

### 16. weather-v1 (`skills/weather/`)
- **Dosya**: `weather_skill.py`
- **Tetikleyiciler**: "hava", "weather", "sicaklik", "yagmur"
- **Islev**: Hava durumu sorgulama

### 17. whatsapp-v1 (`skills/whatsapp/`)
- **Dosya**: `whatsapp_skill.py`
- **Tetikleyiciler**: "whatsapp", "mesaj", "iletisim"
- **Islev**: WhatsApp mesaj gonderme, kisi kaydetme

### 18. youtube-v1 (`skills/youtube/`)
- **Dosya**: `youtube_skill.py`
- **Tetikleyiciler**: "youtube", "video", "kanal"
- **Islev**: YouTube kanal istatistikleri, video arama
- **Islev**: JARVIS hata ayiklama ve durum bilgisi

---

## Action vs Skill Karsilastirmasi

| | Action Modulu | Skill Modulu |
|---|---|---|
| **Kim cagirir?** | AI (function_call) | SkillManager, AI'dan once |
| **AI dahil mi?** | Evet, AI dusunur sonra cagirir | Hayir, aninda calisir |
| **Hiz** | ~1-3sn (AI dusunme suresi) | ~1-10ms |
| **Kayit** | tool_registry.py (tek kaynak) | skills/ klasoru + route fonksiyonu |
| **Kullanim** | Karmasik, baglam gerektiren isler | Basit, ongorulebilir komutlar |

---

## Yeni Skill Ekleme Adimlari

### 1. Klasor ve Dosya Olustur

```bash
mkdir skills/yeni_skill/
touch skills/yeni_skill/yeni_skill.py
```

### 2. Route Fonksiyonunu Yaz

```python
# skills/yeni_skill/yeni_skill.py
import re

TRIGGERS = {
    "action_name": [
        r"(?:tetikleyici|keyword).*?(?:ornek|pattern)",
        r"(?:trigger|keyword)",
    ],
}

def route_yeni_skill_request(user_text: str) -> str | None:
    text = user_text.lower()
    for action, patterns in TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                # Skill mantigini burada calistir
                return f"Skill sonucu: {action}"
    return None
```

### 3. Opsiyonel: SKILL.md Ekle

```yaml
---
SKILL_ID: yeni_skill-v1
SKILL_NAME: "Yeni Skill"
SKILL_VERSION: "1.0"
---
# Yeni Skill
```

### 4. Test Et

```bash
python -c "from core.skill_manager import get_skill_manager; sm = get_skill_manager(); print(sm.list_skills())"
```

SkillManager otomatik kesfeder, kayit gerekmez. Hot-reload ile aninda yuklenir.
