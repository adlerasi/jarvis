# J.A.R.V.I.S — Tool Registry Referansi

> 41 aracin tam listesi, parametreleri, handler haritasi.

---

## Tool Registry Mimarisi (`core/tool_registry.py`)

### Veri Akisi

```
_TOOL_DEFS  (tuple: name, description, params_dict, required_list)
    |
    +-- generate_gemini_declarations() --> Gemini function_declarations
    +-- generate_ollama_tool_help()    --> Ollama system prompt metni
    +-- VALID_TOOLS set                --> Tool adi whitelist
    +-- TOOL_HANDLER_MAP               --> {name: handler_metodu}
```

### Kayit Formati

Her tool bir tuple olarak kaydedilir:

```python
(
    "tool_name",                    # Araci adi
    "Araci aciklamasi...",          # Aciklama
    {                               # Parametreler
        "param1": ("TYPE", "Aciklama"),
        "param2": ("TYPE", "Aciklama"),
    },
    ["param1"],                     # Zorunlu parametreler
)
```

---

## 44 Aracin Tam Listesi

### Temel Araclar

#### 1. open_app
- **Aciklama**: Windows'ta herhangi bir uygulamayi acar (Spotify, Edge, Terminal, VS Code)
- **Parametreler**:
  - `app_name` (STRING, zorunlu) — Uygulama adi
- **Handler**: `_handle_open_app`
- **Modul**: `actions/open_app.py`

#### 2. sys_info
- **Aciklama**: Sistem bilgisi alir: pil, CPU, RAM, disk, saat, tarih, ag
- **Parametreler**:
  - `query` (STRING, zorunlu) — `battery | cpu | ram | disk | time | date | network | all`
- **Handler**: `_handle_sys_info`
- **Modul**: `actions/sys_info.py`

#### 3. get_weather
- **Aciklama**: Anlik hava durumunu ozetler (varsayilan Istanbul)
- **Parametreler**:
  - `location` (STRING, opsiyonel) — Sehir veya konum
- **Handler**: `_handle_get_weather`
- **Modul**: `actions/weather.py`

#### 4. get_current_location
- **Aciklama**: IP adresine gore yaklasik konum bilgisi (sehir, bolge, ulke)
- **Parametreler**: Yok
- **Handler**: `_handle_get_current_location`
- **Modul**: `actions/location.py`

### Takvim ve Hatirlatici

#### 5. get_calendar_events
- **Aciklama**: Windows yerel takvimini okur
- **Parametreler**:
  - `query` (STRING, zorunlu) — `today | tomorrow | next | agenda | week`
  - `limit` (NUMBER, opsiyonel) — Maksimum etkinlik sayisi
- **Handler**: `_handle_get_calendar_events`
- **Modul**: `actions/calendar.py`

#### 6. add_calendar_event
- **Aciklama**: Windows takvimine yeni etkinlik ekler
- **Parametreler**:
  - `title` (STRING, zorunlu) — Baslik
  - `start_iso` (STRING, zorunlu) — Baslangic (ISO veya yyyy-MM-dd HH:mm)
  - `end_iso` (STRING, opsiyonel) — Bitis
  - `location` (STRING, opsiyonel) — Konum
  - `notes` (STRING, opsiyonel) — Notlar
  - `calendar_name` (STRING, opsiyonel) — Takvim adi
  - `all_day` (BOOLEAN, opsiyonel) — Tum gun etkinligi
- **Handler**: `_handle_add_calendar_event`
- **Modul**: `actions/calendar.py`

#### 7. delete_calendar_event
- **Aciklama**: Windows takviminden etkinlik siler
- **Parametreler**:
  - `title` (STRING, zorunlu) — Silinecek baslik
  - `start_iso` (STRING, opsiyonel) — Tarih/saat
  - `calendar_name` (STRING, opsiyonel) — Takvim adi
  - `delete_all_matches` (BOOLEAN, opsiyonel) — Tum eslesenleri sil
- **Handler**: `_handle_delete_calendar_event`
- **Modul**: `actions/calendar.py`

#### 8. get_reminders
- **Aciklama**: Hatirlatmalari listeler
- **Parametreler**:
  - `query` (STRING, zorunlu) — `today | upcoming | overdue | all | next`
  - `limit` (NUMBER, opsiyonel) — Maksimum sayi
  - `list_name` (STRING, opsiyonel) — Liste adi
- **Handler**: `_handle_get_reminders`
- **Modul**: `actions/reminders.py`

#### 9. add_reminder
- **Aciklama**: Yeni hatirlatma ekler
- **Parametreler**:
  - `title` (STRING, zorunlu) — Baslik
  - `due_iso` (STRING, opsiyonel) — Tarih/saat
  - `notes` (STRING, opsiyonel) — Not
  - `list_name` (STRING, opsiyonel) — Liste adi
  - `priority` (STRING, opsiyonel) — `low | medium | high`
- **Handler**: `_handle_add_reminder`
- **Modul**: `actions/reminders.py`

### Tarayici ve Medya

#### 10. browser_control
- **Aciklama**: Tarayici kontrolu (URL acma, Google arama, YouTube)
- **Parametreler**:
  - `action` (STRING, zorunlu) — `open_url | google_search | play_youtube`
  - `url` (STRING, opsiyonel) — URL
  - `query` (STRING, opsiyonel) — Arama sorgusu
- **Handler**: `_handle_browser_control`
- **Modul**: `actions/browser.py`

#### 11. shell_run
- **Aciklama**: Guvenlik filtreli komut calistirir
- **Parametreler**:
  - `command` (STRING, zorunlu) — Calistirilacak komut
- **Handler**: `_handle_shell_run`
- **Modul**: `actions/shell.py`

#### 12. send_whatsapp_message
- **Aciklama**: WhatsApp mesaji gonderir
- **Parametreler**:
  - `contact` (STRING, zorunlu) — Kisi adi
  - `message` (STRING, zorunlu) — Mesaj
- **Handler**: `_handle_send_whatsapp`
- **Modul**: `actions/whatsapp.py`

#### 13. save_whatsapp_contact
- **Aciklama**: WhatsApp iletisim kaydeder
- **Parametreler**:
  - `name` (STRING, zorunlu) — Kisi adi
  - `phone` (STRING, zorunlu) — Telefon numarasi
- **Handler**: `_handle_save_whatsapp_contact`
- **Modul**: `actions/whatsapp.py`

#### 14. play_media
- **Aciklama**: Medya oynatir (YouTube/Spotify/Apple Music)
- **Parametreler**:
  - `query` (STRING, zorunlu) — Oynatilacak icerik
  - `platform` (STRING, opsiyonel) — Platform
- **Handler**: `_handle_play_media`
- **Modul**: `actions/media.py`

#### 15. get_youtube_channel_report
- **Aciklama**: YouTube kanal raporu alir
- **Parametreler**:
  - `channel_handle` (STRING, opsiyonel) — Kanal handle
- **Handler**: `_handle_get_youtube_channel_report`
- **Modul**: `actions/youtube_stats.py`

#### 16. analyze_screen
- **Aciklama**: Ekran goruntusu alir ve Gemini Vision ile analiz eder
- **Parametreler**:
  - `prompt` (STRING, opsiyonel) — Analiz prompt'u
- **Handler**: `_handle_analyze_screen`
- **Modul**: `actions/screen_vision.py`

### Sistem Araclari

#### 17. get_system_health
- **Aciklama**: Kapsamli sistem saglik raporu
- **Parametreler**: Yok
- **Handler**: `_handle_get_system_health`
- **Modul**: `actions/system_doctor.py`

#### 18. cleanup_temp_files
- **Aciklama**: Gecici dosyalari temizler
- **Parametreler**:
  - `days_old` (NUMBER, opsiyonel) — Gun sayisi
- **Handler**: `_handle_cleanup_temp_files`
- **Modul**: `actions/system_doctor.py`

#### 19. cleanup_recycle_bin
- **Aciklama**: Geri donusum kutusunu bosaltir
- **Parametreler**: Yok
- **Handler**: `_handle_cleanup_recycle_bin`
- **Modul**: `actions/system_doctor.py`

#### 20. list_processes
- **Aciklama**: Calisan surecleri listeler
- **Parametreler**:
  - `sort_by` (STRING, opsiyonel) — Siralama
  - `limit` (NUMBER, opsiyonel) — Sayi siniri
- **Handler**: `_handle_list_processes`
- **Modul**: `actions/process_manager.py`

#### 21. kill_process
- **Aciklama**: Sureci sonlandirir
- **Parametreler**:
  - `pid` (NUMBER, opsiyonel) — PID
  - `name` (STRING, opsiyonel) — Surec adi
- **Handler**: `_handle_kill_process`
- **Modul**: `actions/process_manager.py`

#### 22. set_process_priority
- **Aciklama**: Surec onceligini degistirir
- **Parametreler**:
  - `pid` (NUMBER, zorunlu) — PID
  - `priority` (STRING, zorunlu) — `low | below_normal | normal | above_normal | high | realtime`
- **Handler**: `_handle_set_process_priority`
- **Modul**: `actions/process_manager.py`

#### 23. find_process_by_port
- **Aciklama**: Port numarasina gore surec bulur
- **Parametreler**:
  - `port` (NUMBER, zorunlu) — Port numarasi
- **Handler**: `_handle_find_process_by_port`
- **Modul**: `actions/process_manager.py`

### Dosya Araclari

#### 24. find_large_files
- **Aciklama**: Buyuk dosyalari bulur
- **Parametreler**:
  - `folder` (STRING, opsiyonel) — Klasor
  - `min_gb` (NUMBER, opsiyonel) — Minimum GB
- **Handler**: `_handle_find_large_files`
- **Modul**: `actions/file_guardian.py`

#### 25. find_duplicate_files
- **Aciklama**: Yinelenen dosyalari tespit eder
- **Parametreler**:
  - `folder` (STRING, opsiyonel) — Klasor
- **Handler**: `_handle_find_duplicate_files`
- **Modul**: `actions/file_guardian.py`

#### 26. cleanup_folder
- **Aciklama**: Klasordeki eski dosyalari temizler
- **Parametreler**:
  - `folder` (STRING, zorunlu) — Klasor
  - `days_old` (NUMBER, opsiyonel) — Gun sayisi
- **Handler**: `_handle_cleanup_folder`
- **Modul**: `actions/file_guardian.py`

#### 27. get_folder_summary
- **Aciklama**: Klasor ozetini cikarir
- **Parametreler**:
  - `folder` (STRING, opsiyonel) — Klasor
- **Handler**: `_handle_get_folder_summary`
- **Modul**: `actions/file_guardian.py`

### Ag Araclari

#### 28. get_network_summary
- **Aciklama**: Ag ozet bilgisi (IP, bant genisligi)
- **Parametreler**: Yok
- **Handler**: `_handle_get_network_summary`
- **Modul**: `actions/network_monitor.py`

#### 29. list_net_connections
- **Aciklama**: Ag baglantilarini listeler
- **Parametreler**:
  - `state` (STRING, opsiyonel) — Durum filtresi
- **Handler**: `_handle_list_net_connections`
- **Modul**: `actions/network_monitor.py`

#### 30. ping_host
- **Aciklama**: Ping testi yapar
- **Parametreler**:
  - `host` (STRING, zorunlu) — Hedef host
- **Handler**: `_handle_ping_host`
- **Modul**: `actions/network_monitor.py`

### Zamanlanmis Gorevler

#### 31. add_cron_job
- **Aciklama**: Zamanlanmis gorev ekler
- **Parametreler**:
  - `name` (STRING, zorunlu) — Gorev adi
  - `interval_m` (NUMBER, zorunlu) — Dakika araligi
  - `command` (STRING, zorunlu) — Calistirilacak komut
- **Handler**: `_handle_add_cron_job`
- **Modul**: `actions/system_cron.py`

#### 32. list_cron_jobs
- **Aciklama**: Zamanlanmis gorevleri listeler
- **Parametreler**: Yok
- **Handler**: `_handle_list_cron_jobs`
- **Modul**: `actions/system_cron.py`

#### 33. remove_cron_job
- **Aciklama**: Zamanlanmis gorev siler
- **Parametreler**:
  - `name` (STRING, zorunlu) — Gorev adi
- **Handler**: `_handle_remove_cron_job`
- **Modul**: `actions/system_cron.py`

#### 34. toggle_cron_job
- **Aciklama**: Gorevi acar/kapatir
- **Parametreler**:
  - `name` (STRING, zorunlu) — Gorev adi
- **Handler**: `_handle_toggle_cron_job`
- **Modul**: `actions/system_cron.py`

#### 35. start_cron_daemon
- **Aciklama**: Cron servisini baslatir
- **Parametreler**: Yok
- **Handler**: `_handle_start_cron_daemon`
- **Modul**: `actions/system_cron.py`

### Servis Araclari

#### 36. list_services
- **Aciklama**: Sistem servislerini listeler
- **Parametreler**: Yok
- **Handler**: `_handle_list_services`
- **Modul**: `actions/service_monitor.py`

#### 37. control_service
- **Aciklama**: Servisi baslatir/durdurur/yeniden baslatir
- **Parametreler**:
  - `name` (STRING, zorunlu) — Servis adi
  - `action` (STRING, zorunlu) — `start | stop | restart`
- **Handler**: `_handle_control_service`
- **Modul**: `actions/service_monitor.py`

### Ajan Araclari

#### 38. agent_execute_goal
- **Aciklama**: Otonom ajan gorevi baslatir (alt-ajan yonetimi)
- **Parametreler**:
  - `goal` (STRING, zorunlu) — Hedef
  - `context` (STRING, opsiyonel) — Baglam
- **Handler**: `_handle_agent_execute_goal`
- **Modul**: `core/skill_manager.py`

#### 39. browser_skill
- **Aciklama**: Skill tabanli tarayici kontrolu (AI olmadan)
- **Parametreler**:
  - `action` (STRING, zorunlu) — `open | search | play`
  - `query` (STRING, opsiyonel) — Sorgu/URL
- **Handler**: `_handle_browser_skill`
- **Modul**: `skills/browser/browser_skill.py`

### Ses ve Medya

#### 40. set_volume
- **Aciklama**: Sistem ses seviyesini ayarlar (0-100)
- **Parametreler**:
  - `level` (NUMBER, zorunlu) — 0-100 arasi
- **Handler**: `_handle_set_volume`
- **Modul**: `main.py` (yerel)

#### 41. capture_camera
- **Aciklama**: Kameradan goruntu yakalar
- **Parametreler**: Yok
- **Handler**: `_handle_capture_camera`
- **Modul**: `actions/screen_vision.py`

### Bellek Araclari

#### 42. get_memory
- **Aciklama**: Kullanici belleginden deger okur
- **Parametreler**:
  - `key` (STRING, opsiyonel) — Bellek anahtari
- **Handler**: `_handle_get_memory`
- **Modul**: `memory/memory_manager.py`

#### 43. save_memory
- **Aciklama**: Kullanici bellegine deger yazar
- **Parametreler**:
  - `key` (STRING, zorunlu) — Bellek anahtari
  - `value` (STRING, zorunlu) — Deger
- **Handler**: `_handle_save_memory`
- **Modul**: `memory/memory_manager.py`

#### 44. delete_memory
- **Aciklama**: Kullanici belleginden deger siler
- **Parametreler**:
  - `key` (STRING, zorunlu) — Bellek anahtari
- **Handler**: `_handle_delete_memory`
- **Modul**: `memory/memory_manager.py`

---

## Tool Handler Haritasi

```python
_TOOL_HANDLERS = {
    "add_calendar_event": "_handle_add_calendar_event",
    "add_cron_job": "_handle_add_cron_job",
    "add_reminder": "_handle_add_reminder",
    "agent_execute_goal": "_handle_agent_execute_goal",
    "analyze_screen": "_handle_analyze_screen",
    "browser_control": "_handle_browser_control",
    "browser_skill": "_handle_browser_skill",
    "capture_camera": "_handle_capture_camera",
    "cleanup_folder": "_handle_cleanup_folder",
    "cleanup_recycle_bin": "_handle_cleanup_recycle_bin",
    "cleanup_temp_files": "_handle_cleanup_temp_files",
    "control_service": "_handle_control_service",
    "delete_calendar_event": "_handle_delete_calendar_event",
    "delete_memory": "_handle_delete_memory",
    "find_duplicate_files": "_handle_find_duplicate_files",
    "find_large_files": "_handle_find_large_files",
    "find_process_by_port": "_handle_find_process_by_port",
    "get_calendar_events": "_handle_get_calendar_events",
    "get_current_location": "_handle_get_current_location",
    "get_folder_summary": "_handle_get_folder_summary",
    "get_memory": "_handle_get_memory",
    "get_network_summary": "_handle_get_network_summary",
    "get_reminders": "_handle_get_reminders",
    "get_system_health": "_handle_get_system_health",
    "get_weather": "_handle_get_weather",
    "get_youtube_channel_report": "_handle_get_youtube_channel_report",
    "kill_process": "_handle_kill_process",
    "list_cron_jobs": "_handle_list_cron_jobs",
    "list_net_connections": "_handle_list_net_connections",
    "list_processes": "_handle_list_processes",
    "list_services": "_handle_list_services",
    "open_app": "_handle_open_app",
    "ping_host": "_handle_ping_host",
    "play_media": "_handle_play_media",
    "remove_cron_job": "_handle_remove_cron_job",
    "save_memory": "_handle_save_memory",
    "save_whatsapp_contact": "_handle_save_whatsapp_contact",
    "send_whatsapp_message": "_handle_send_whatsapp_message",
    "set_process_priority": "_handle_set_process_priority",
    "set_volume": "_handle_set_volume",
    "shell_run": "_handle_shell_run",
    "start_cron_daemon": "_handle_start_cron_daemon",
    "sys_info": "_handle_sys_info",
    "toggle_cron_job": "_handle_toggle_cron_job",
}
```

---

## Yeni Tool Ekleme

### 1. Tool Tanimini Ekle

`core/tool_registry.py` -> `_TOOL_DEFS` listesine yeni tuple:

```python
(
    "yeni_arac",
    "Aracin aciklamasi...",
    {"param1": ("STRING", "Parametre aciklamasi")},
    ["param1"],
)
```

### 2. Handler Metodunu Ekle

`main.py`'ye yeni handler metodu:

```python
async def _handle_yeni_arac(self, args: dict, loop) -> str:
    """Yeni arac handler'i."""
    param = args.get("param1", "")
    sonuc = actions.yeni_modul.fonksiyon(param)
    return str(sonuc)
```

### 3. Handler Haritasina Ekle

```python
_TOOL_HANDLERS["yeni_arac"] = "_handle_yeni_arac"
```

### 4. Test Ekle

```python
def test_yeni_arac(self):
    """Yeni arac dogru calismali."""
    result = yeni_modul.fonksiyon("test")
    self.assertIsNotNone(result)
```

### Onemli Kurallar

1. Handler imzasi: `async def _handle_<name>(self, args, loop) -> str`
2. args: dict (tool parametreleri)
3. loop: asyncio event loop (thread pool gerekiyorsa)
4. Donus: string (UI'da gosterilecek)
5. Asla `elif` zinciri kullanma - sadece dict dispatch
