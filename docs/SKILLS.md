# Skill Sistemi

## Skill Mimarisi

JARVIS Skill Sistemi, kullanıcı komutlarını **LLM'e göndermeden önce** işleyen bir routing katmanıdır. Amaç: basit, öngörülebilir komutlara anında yanıt vermek (1-5ms), LLM gecikmesini (~1-3sn) ortadan kaldırmak.

```
Kullanıcı komutu
    │
    ├── SkillManager.route(text)
    │       │
    │       ├── EŞLEŞTİ → Skill doğrudan çalışır
    │       │              Sonuç UI'da gösterilir
    │       │              LLM'e gidilmez
    │       │
    │       └── EŞLEŞMEDİ → Normal LLM akışına devam
```

### Skill vs Action Farkı

| Özellik | Action Modülü | Skill Modülü |
|---------|---------------|--------------|
| **Kim çağırır?** | AI (function_call) | SkillManager, AI'dan önce |
| **AI dahil mi?** | Evet, AI düşünür sonra çağırır | Hayır, anında çalışır |
| **Hız** | ~1-3sn (AI düşünme süresi) | ~1-5ms |
| **Kayıt** | `tool_registry.py` + `_TOOL_HANDLERS` | `skills/` klasörü + route fonksiyonu |
| **Kullanım** | Karmaşık, bağlam gerektiren işler | Basit, öngörülebilir komutlar |
| **State** | request/response | Stateless |

## Skill Yükleme Mekanizması

### SkillEngine (`core/_skill_engine.py`)

```python
class SkillEngine:
    """
    Dinamik skill yükleyici.
    - skills/ klasörünü runtime'da tarar
    - Her skill modülünü dynamic import ile yükler
    - 3sn interval ile hot-reload yapar
    """
    
    def _discover_skills(self, skills_dir: Path) -> None:
        for folder in sorted(skills_dir.iterdir()):
            if not folder.is_dir():
                continue
            # <name>_skill.py dosyasını ara
            skill_files = list(folder.glob("*_skill.py"))
            if not skill_files:
                continue
            for sf in skill_files:
                self._load_skill(sf)
```

### Dinamik Yükleme (Runtime)

```python
def _load_skill(self, module_path: Path) -> SkillInfo | None:
    # 1. Modül adını çöz
    spec = importlib.util.spec_from_file_location(skill_id, module_path)
    mod = importlib.util.module_from_spec(spec)
    
    # 2. route fonksiyonunu bul
    route_func = getattr(mod, f"route_{skill_id}_request", None)
    
    # 3. Metadata oku
    md_path = module_path.parent / "SKILL.md"
    triggers_path = module_path.parent / "triggers.json"
    
    # 4. Kaydet
    self._skills[skill_id] = SkillInfo(...)
```

### Hot-Reload Döngüsü

```python
# Watcher thread — 3sn interval
def _watch_skills(self):
    while self._running:
        self._check_for_changes()
        time.sleep(3)

def _check_for_changes(self):
    current = self._scan_skills_dir()
    for skill_id, mtime in current.items():
        if skill_id not in self._skill_mtimes:
            self._load_skill(...)          # YENİ
        elif mtime > self._skill_mtimes[skill_id]:
            self._reload_skill(...)        # DEĞİŞEN
    for skill_id in self._skill_mtimes:
        if skill_id not in current:
            self._unload_skill(...)        # SİLİNEN
```

### Skill Keşif Protokolü

```
skills/<name>/
├── <name>_skill.py        ← ZORUNLU: route_<name>_request(user_text)
├── SKILL.md               ← OPSİYONEL: YAML frontmatter (metadata)
└── triggers.json          ← OPSİYONEL: trigger pattern'leri
```

## Mevcut Skill'ler

| Skill ID | Klasör | Amaç | Versiyon |
|----------|--------|------|----------|
| `browser` | skills/browser/ | URL açma, arama, YouTube oynatma | 1.0 |
| `system_health` | skills/system_health/ | CPU/RAM/disk sağlık kontrolü | 1.0 |
| `process_control` | skills/process_control/ | Süreç listeleme/öldürme | 1.0 |
| `file_manager` | skills/file_manager/ | Dosya yönetimi | 1.0 |
| `network` | skills/network/ | Ağ izleme | 1.0 |
| `scheduler` | skills/scheduler/ | Zamanlanmış görevler | 1.0 |
| `services` | skills/services/ | Servis yönetimi | 1.0 |
| `weather` | skills/weather/ | Hava durumu sorgulama | 1.0 |
| `youtube` | skills/youtube/ | YouTube istatistikleri + oynatma | 1.0 |
| `vision` | skills/vision/ | Ekran görüntüsü analizi | 1.0 |
| `calendar` | skills/calendar/ | Takvim yönetimi | 1.0 |
| `reminders` | skills/reminders/ | Hatırlatıcı yönetimi | 1.0 |
| `whatsapp` | skills/whatsapp/ | WhatsApp mesajlaşma | 1.0 |
| `media` | skills/media/ | Medya oynatma | 1.0 |
| `demo` | skills/demo/ | Demo/örnek skill | 0.1 |
| `greeting` | skills/greeting/ | Selamlama yanıtları | 1.0 |
| `debugging_jarvis` | skills/debugging_jarvis/ | JARVIS hata ayıklama | 1.0 |

### Skill: `browser`

- **Amaç:** URL açma, Google arama, YouTube oynatma
- **Tetikleyici Komutlar:** "youtube aç", "google'da ara", "github aç", "siteye git"
- **Giriş Parametreleri:** `action: str`, `url: str | None`, `query: str | None`
- **İş Akışı:**
  1. Kullanıcı metnini regex pattern'leriyle eşleştir
  2. Aksiyon tipini belirle (open_url / search / play_youtube)
  3. `browser_control()` action fonksiyonunu çağır
  4. Sonucu string olarak döndür
- **Kullandığı Harici API/Kütüphane:** `actions.browser` → `webbrowser`
- **Başarı/Hata Durumları:** Başarı → "X açılıyor...", Hata → yakalanamayan URL hatası
- **Kod Lokasyonu:** `skills/browser/browser_skill.py`

### Skill: `weather`

- **Amaç:** Anlık hava durumu sorgulama
- **Tetikleyici Komutlar:** "hava durumu", "hava nasıl", "weather"
- **İş Akışı:** Regex eşleşme → `get_weather_summary()` → sonucu formatla
- **Kullandığı Harici API/Kütüphane:** wttr.in API
- **Kod Lokasyonu:** `skills/weather/weather_skill.py`

## Skill Geliştirme Rehberi

### Yeni Skill Ekleme

```python
# skills/yeni_skill/yeni_skill.py
import re

# OPSİYONEL: Inline trigger desenleri
TRIGGERS = {
    "action_name": [
        r"(?:tetikleyici|keyword).*?(?:ornek|pattern)",
    ],
}

# ZORUNLU: Routing fonksiyonu — "route_<klasor_adi>_request"
def route_yeni_skill_request(user_text: str) -> str | None:
    """user_text'te trigger ara, eşleşirse skill çalıştır."""
    text = user_text.lower()
    
    # Inline triggers
    for action, patterns in TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return f"Skill sonucu: {action}"
    
    # İsteğe bağlı: triggers.json'dan yükleme
    return None
```

### Kurallar

1. **Fonksiyon adı:** `route_<klasor_adi>_request(user_text) → str | None`
   - `str` dönerse → skill eşleşti, sonuç bu
   - `None` dönerse → skill eşleşmedi, diğer skill'lere/LLM'e geç
2. **Klasör yapısı:** `skills/<name>/<name>_skill.py`
3. **Türkçe karakter:** ASCII fallback ekleyin: `(?:goster|göster)`
4. **Hot-reload:** Dosya değişince otomatik yeniden yüklenir
5. **Kayıt gerekmez:** SkillManager otomatik keşfeder

### Skill Manager Singleton

```python
# core/skill_manager.py
def get_skill_manager() -> SkillManager:
    """Tekil SkillManager örneğini döndür."""
    global _SM_INSTANCE
    if _SM_INSTANCE is None:
        _SM_INSTANCE = SkillManager()
    return _SM_INSTANCE
```

## Skill → LLM Entegrasyonu

Skill sistemi LLM'den **bağımsız** çalışır. İkisi arasında doğrudan iletişim yoktur:

```
main.py._on_text_command()
    │
    ├── SkillManager.route(text) → str | None
    │       ├── str → Skill çalıştı, sonuç UI'da göster
    │       └── None → Provider.send_text(text) → LLM
    │
    └── Eşleşme yoksa LLM tool call'ları ile action modülleri
```

Bu tasarımın avantajları:
- **Gecikme yok:** Basit komutlar anında çalışır
- **Offline çalışma:** İnternet olmasa bile skill'ler çalışır
- **Güvenlik:** Skill'ler AI'nın öngörülemezliğinden etkilenmez
- **Deterministik:** Aynı komut her zaman aynı sonucu üretir

[Bkz. ORCHESTRATOR.md](ORCHESTRATOR.md) | [Bkz. AGENTS.md](AGENTS.md) | [Bkz. UI_LAYER.md](UI_LAYER.md)
