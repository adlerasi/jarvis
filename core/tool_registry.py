# ── Tool Registry ────────────────────────────────────────────
# Single source of truth for ALL tools in J.A.R.V.I.S.
# Generates:
#   → Gemini function_declarations format
#   → Ollama text-based tool list (for system prompt)
#   → valid_tools whitelist
#   → handler dispatch map
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import json
from typing import Any


# ── Canonical Tool Definitions ──────────────────────────────
# Each entry: (name, description, params_dict, required_list)
# params_dict: { param_name: (type_str, description_str), ... }

_TOOL_DEFS: list[tuple[str, str, dict[str, tuple[str, str]], list[str]]] = [
    # ── Temel Araçlar ──
    ("open_app",
        "Windows'ta herhangi bir uygulamayi acar. Spotify, Edge, Terminal, Explorer, VS Code vb.",
        {"app_name": ("STRING", "Uygulama adı (örn. 'Spotify', 'Edge', 'Terminal')")},
        ["app_name"]),

    ("sys_info",
        "Sistem bilgisi alır: pil durumu, CPU, RAM, disk, saat, tarih, ağ bağlantısı.",
        {"query": ("STRING", "battery | cpu | ram | disk | time | date | network | all")},
        ["query"]),

    ("get_weather",
        "Anlik hava durumunu ozetler. Varsayilan konum Istanbul'dur.",
        {"location": ("STRING", "Sehir veya konum. Bos birakilirsa Istanbul kullanilir.")},
        []),

    ("get_current_location",
        "IP adresine gore yaklasik konum bilgisini verir (sehir, bolge, ulke).",
        {},
        []),

    ("get_calendar_events",
        "Windows yerel takvimini okur. Bugun, yarin, siradaki etkinlik veya yaklasan ajandayi ozetler.",
        {"query": ("STRING", "today | tomorrow | next | agenda | week veya dogal dilde"),
         "limit": ("NUMBER", "Maksimum etkinlik sayisi")},
        ["query"]),

    ("add_calendar_event",
        "Windows yerel takvimine yeni etkinlik ekler.",
        {"title": ("STRING", "Etkinlik basligi"),
         "start_iso": ("STRING", "Baslangic tarih/saat. ISO veya yyyy-MM-dd HH:mm formatinda."),
         "end_iso": ("STRING", "Bitis tarih/saat. Opsiyonel."),
         "location": ("STRING", "Etkinlik konumu. Opsiyonel."),
         "notes": ("STRING", "Etkinlik notlari. Opsiyonel."),
         "calendar_name": ("STRING", "Eklenecek takvim adi. Opsiyonel."),
         "all_day": ("BOOLEAN", "true ise tum gun etkinligi olusturur.")},
        ["title", "start_iso"]),

    ("delete_calendar_event",
        "Windows yerel takviminden etkinlik siler.",
        {"title": ("STRING", "Silinecek etkinlik basligi"),
         "start_iso": ("STRING", "Opsiyonel tarih/saat. Ayni isimli birden fazla etkinligi ayirt etmek icin."),
         "calendar_name": ("STRING", "Opsiyonel takvim adi"),
         "delete_all_matches": ("BOOLEAN", "true ise eslesen tum etkinlikleri siler")},
        ["title"]),

    ("get_reminders",
        "Hatirlatmalari listeler. Bugunku, yaklasan, geciken veya tum aciklari ozetler.",
        {"query": ("STRING", "today | upcoming | overdue | all | next"),
         "limit": ("NUMBER", "Maksimum hatirlatici sayisi"),
         "list_name": ("STRING", "Istenirse belirli bir liste adi")},
        ["query"]),

    ("add_reminder",
        "Yeni bir hatirlatma ekler.",
        {"title": ("STRING", "Hatirlatma basligi"),
         "due_iso": ("STRING", "Opsiyonel tarih/saat. Ornek: 2026-04-13T09:00"),
         "notes": ("STRING", "Opsiyonel not"),
         "list_name": ("STRING", "Opsiyonel liste adi"),
         "priority": ("STRING", "low | medium | high"),
         "all_day": ("BOOLEAN", "Tum gun hatirlatici ise true")},
        ["title"]),

    ("browser_control",
        "Tarayıcıda URL açar, Google'da arama yapar veya YouTube'da ilk sonucu oynatır.",
        {"action": ("STRING", "open_url | search | play_youtube"),
         "url": ("STRING", "Açılacak URL (open_url için)"),
         "query": ("STRING", "Arama sorgusu (search veya play_youtube için)")},
        ["action"]),

    ("browser_skill",
        "Browser skill - Tarayici kontrolu icin gelismis skill. URL acma, Google arama, YouTube oynatma.",
        {"action": ("STRING", "open_url | search | play_youtube"),
         "target": ("STRING", "URL, arama sorgusu veya video adi")},
        ["action", "target"]),

    ("shell_run",
        "Komut çalıştırır. Dosya işlemleri, sistem yönetimi.",
        {"command": ("STRING", "Çalıştırılacak komut")},
        ["command"]),

    ("play_media",
        "YouTube, Spotify veya web muzik servislerinde sarki, muzik veya video acar.",
        {"query": ("STRING", "Şarkı, sanatçı, albüm veya video arama ifadesi"),
         "provider": ("STRING", "auto | youtube | spotify | apple_music"),
         "autoplay": ("BOOLEAN", "true ise mümkünse doğrudan oynatır")},
        ["query"]),

    ("get_youtube_channel_report",
        "YouTube kanalinin public istatistiklerini ve son videolarin performansini raporlar.",
        {"query": ("STRING", "Dogal dilde analiz istegi"),
         "handle": ("STRING", "Opsiyonel kanal handle'i veya ID'si"),
         "video_limit": ("NUMBER", "Analize dahil edilecek son video sayisi")},
        ["query"]),

    ("analyze_screen",
        "Aktif pencerenin ekran goruntusunu alip Gemini vision ile analiz eder.",
        {"query": ("STRING", "Kullanicinin ekranla ilgili sorusu"),
         "target": ("STRING", "Su an sadece active_window desteklenir.")},
        ["query"]),

    ("capture_camera",
        "Kameradan fotograf ceker ve Gemini vision ile analiz eder.",
        {"query": ("STRING", "Kameradaki goruntuyle ilgili soru")},
        []),

    ("save_memory",
        "Kullanıcı hakkında önemli bilgiyi kalıcı belleğe kaydeder.",
        {"category": ("STRING", "identity | preferences | projects | notes"),
         "key": ("STRING", "Kısa anahtar (örn. 'name')"),
         "value": ("STRING", "Değer")},
        ["category", "key", "value"]),

    ("delete_memory",
        "Kalici hafizadaki bir kaydi siler.",
        {"category": ("STRING", "Kaydin kategorisi"),
         "key": ("STRING", "Silinecek anahtar"),
         "match_text": ("STRING", "Kaydi bulmak icin dogal dil parcasi")},
        []),

    ("send_whatsapp_message",
        "WhatsApp üzerinden mesaj gönderir.",
        {"recipient_name": ("STRING", "Kişi adı"),
         "phone_number": ("STRING", "Uluslararası telefon numarası"),
         "message": ("STRING", "Mesaj içeriği"),
         "app_target": ("STRING", "desktop | web | auto"),
         "send_now": ("BOOLEAN", "true ise mesaji otomatik gönderir")},
        ["message"]),

    ("save_whatsapp_contact",
        "Sık kullanılan WhatsApp kişisini kalıcı belleğe kaydeder.",
        {"display_name": ("STRING", "Kaydedilecek kişi adı"),
         "phone_number": ("STRING", "Uluslararası telefon numarası"),
         "aliases": ("STRING", "Virgülle ayrılmış alternatif hitaplar")},
        ["display_name", "phone_number"]),

    # ── Sistem Sağlığı ──
    ("get_system_health",
        "Sistem sağlık raporu üretir: Disk, RAM, CPU, ağ, başlangıç, süreçler, sıcaklık.",
        {"query": ("STRING", "all | disk | memory | cpu | network | startup | processes | temperature")},
        []),

    ("cleanup_temp_files",
        "Temp klasörünü temizler.",
        {},
        []),

    ("cleanup_recycle_bin",
        "Geri dönüşüm kutusunu boşaltır.",
        {},
        []),

    # ── Süreç Yönetimi ──
    ("list_processes",
        "Çalışan süreçleri listeler.",
        {"sort_by": ("STRING", "cpu | memory | name | pid"),
         "limit": ("NUMBER", "Kaç süreç gösterilecek")},
        []),

    ("kill_process",
        "Bir süreç sonlandırır.",
        {"identifier": ("STRING", "Süreç adı veya PID"),
         "force": ("BOOLEAN", "True ise zorla öldürür")},
        ["identifier"]),

    ("set_process_priority",
        "Süreç önceliğini ayarlar.",
        {"identifier": ("STRING", "Süreç adı veya PID"),
         "priority": ("STRING", "high | normal | low | realtime | idle")},
        ["identifier", "priority"]),

    ("find_process_by_port",
        "Belirli bir portu kullanan süreçleri bulur.",
        {"port": ("NUMBER", "Port numarası")},
        ["port"]),

    # ── Dosya Yönetimi ──
    ("find_large_files",
        "Büyük dosyaları bulur.",
        {"path": ("STRING", "Aranacak klasör yolu"),
         "min_size_mb": ("NUMBER", "Minimum dosya boyutu MB"),
         "limit": ("NUMBER", "Maksimum sonuç")},
        []),

    ("find_duplicate_files",
        "Yinelenen dosyaları bulur.",
        {"path": ("STRING", "Aranacak klasör yolu"),
         "limit": ("NUMBER", "Maksimum sonuç")},
        []),

    ("cleanup_folder",
        "Klasördeki dosyaları temizler.",
        {"path": ("STRING", "Temizlenecek klasör yolu"),
         "pattern": ("STRING", "Dosya deseni"),
         "dry_run": ("BOOLEAN", "True ise sadece raporlar")},
        ["path"]),

    ("get_folder_summary",
        "Klasör özet istatistikleri.",
        {"path": ("STRING", "Klasör yolu")},
        []),

    # ── Ağ İzleme ──
    ("get_network_summary",
        "Ağ özet raporu.",
        {},
        []),

    ("list_net_connections",
        "Ağ bağlantılarını listeler.",
        {"state": ("STRING", "all | established | listen | close_wait | time_wait"),
         "limit": ("NUMBER", "Maksimum sonuç")},
        []),

    ("ping_host",
        "Ping testi yapar.",
        {"host": ("STRING", "Hedef host"),
         "count": ("NUMBER", "Ping sayısı")},
        []),

    # ── Zamanlanmış Görevler ──
    ("add_cron_job",
        "Zamanlanmış görev ekler.",
        {"name": ("STRING", "Görev adı"),
         "command": ("STRING", "temp_cleanup | health_check | sys_info | shell_run"),
         "schedule_type": ("STRING", "once | daily | weekly | interval"),
         "schedule_value": ("STRING", "once: ISO datetime | daily: HH:MM | weekly: D-HH:MM | interval: saniye")},
        ["name", "command", "schedule_type", "schedule_value"]),

    ("list_cron_jobs",
        "Zamanlanmış görevleri listeler.",
        {"enabled_only": ("BOOLEAN", "Sadece aktif görevleri göster")},
        []),

    ("remove_cron_job",
        "Zamanlanmış görevi siler.",
        {"job_id": ("NUMBER", "Görev ID'si")},
        ["job_id"]),

    # ── Servis Yönetimi ──
    ("list_services",
        "Servisleri listeler.",
        {"status_filter": ("STRING", "all | running | stopped | auto | manual"),
         "limit": ("NUMBER", "Maksimum sonuç")},
        []),

    ("control_service",
        "Servisi kontrol eder: baslat, durdur, yeniden baslat.",
        {"service_name": ("STRING", "Servis adı"),
         "action": ("STRING", "start | stop | restart | status")},
        ["service_name", "action"]),

    # ── Ses ──
    ("set_volume",
        "Sistem ses seviyesini ayarlar.",
        {"level": ("NUMBER", "Ses seviyesi 0-100 arasi"),
         "action": ("STRING", "set | up | down | mute | unmute")},
        []),

    # ── ACA (Autonomous Computer Agent) ──
    ("agent_execute_goal",
        "Otonom bilgisayar ajanina bir hedef verir. Ajan hedefi adim adim planlar, "
        "ekrani gozlemler, araclari kullanir ve sonucu bildirir. "
        "Ornek: 'Notepad ac ve icine merhaba yaz', 'Hesap makinesini ac ve 15*3 hesaplat'",
        {"goal_text": ("STRING", "Agent'in gerceklestirmesi icin dogal dilde hedef tanimi")},
        ["goal_text"]),
]
# Maps tool name → handler method name on the Jarvis class
# Must be kept in sync with actual handler methods in main.py

TOOL_HANDLER_MAP: dict[str, str] = {
    "save_memory":              "_handle_save_memory",
    "delete_memory":            "_handle_delete_memory",
    "open_app":                 "_handle_open_app",
    "sys_info":                 "_handle_sys_info",
    "get_weather":              "_handle_get_weather",
    "get_calendar_events":      "_handle_get_calendar_events",
    "add_calendar_event":       "_handle_add_calendar_event",
    "delete_calendar_event":    "_handle_delete_calendar_event",
    "get_reminders":            "_handle_get_reminders",
    "add_reminder":             "_handle_add_reminder",
    "browser_control":          "_handle_browser_control",
    "browser_skill":            "_handle_browser_skill",
    "shell_run":                "_handle_shell_run",
    "play_media":               "_handle_play_media",
    "get_youtube_channel_report": "_handle_get_youtube_channel_report",
    "analyze_screen":           "_handle_analyze_screen",
    "capture_camera":           "_handle_capture_camera",
    "send_whatsapp_message":    "_handle_send_whatsapp_message",
    "save_whatsapp_contact":    "_handle_save_whatsapp_contact",
    "get_current_location":     "_handle_get_current_location",
    "get_system_health":        "_handle_get_system_health",
    "cleanup_temp_files":       "_handle_cleanup_temp_files",
    "cleanup_recycle_bin":      "_handle_cleanup_recycle_bin",
    "list_processes":           "_handle_list_processes",
    "kill_process":             "_handle_kill_process",
    "set_process_priority":     "_handle_set_process_priority",
    "find_process_by_port":     "_handle_find_process_by_port",
    "find_large_files":         "_handle_find_large_files",
    "find_duplicate_files":     "_handle_find_duplicate_files",
    "cleanup_folder":           "_handle_cleanup_folder",
    "get_folder_summary":       "_handle_get_folder_summary",
    "get_network_summary":      "_handle_get_network_summary",
    "list_net_connections":     "_handle_list_net_connections",
    "ping_host":                "_handle_ping_host",
    "add_cron_job":             "_handle_add_cron_job",
    "list_cron_jobs":           "_handle_list_cron_jobs",
    "remove_cron_job":          "_handle_remove_cron_job",
    "list_services":            "_handle_list_services",
    "control_service":          "_handle_control_service",
    "set_volume":               "_handle_set_volume",
    "agent_execute_goal":       "_handle_agent_goal",
}

# ── Valid Tools Set ─────────────────────────────────────────
VALID_TOOLS: set[str] = {name for name, *_ in _TOOL_DEFS}

# ── Generator: Gemini function_declarations ─────────────────

def generate_gemini_declarations() -> list[dict[str, Any]]:
    """Generate Gemini Live API function_declarations format."""
    declarations = []
    for name, desc, params, required in _TOOL_DEFS:
        d: dict[str, Any] = {
            "name": name,
            "description": desc,
            "parameters": {"type": "OBJECT", "properties": {}},
        }
        if required:
            d["parameters"]["required"] = list(required)
        for pname, (ptype, pdesc) in params.items():
            d["parameters"]["properties"][pname] = {
                "type": ptype,
                "description": pdesc,
            }
        declarations.append(d)
    return declarations


# ── Generator: Ollama prompt text ───────────────────────────

def generate_ollama_tool_help() -> str:
    """Generate tool descriptions for Ollama system prompt."""
    lines: list[str] = []
    lines.append("\n\n[KULLANILABİLİR ARAÇLAR]")
    lines.append(
        "Aşağıdaki araçlara erişimin var. Bir görevi tamamlamak için uygun aracı çağır.\n"
        "Araç çağrısını normal yanıtın İÇİNDE kullanabilirsin. "
        'Örneğin: "Hemen bakıyorum... get_weather(location=\'İzmir\') şeklinde sorguluyorum..."'
    )

    def _fmt(tool_name: str) -> str:
        return f"  {tool_name}({_params_str(tool_name)})"

    def _params_str(tool_name: str) -> str:
        for name, _, params, _ in _TOOL_DEFS:
            if name == tool_name:
                parts = []
                for pname, (ptype, _) in params.items():
                    if ptype == "STRING":
                        parts.append(f"{pname}='...'")
                    elif ptype == "NUMBER":
                        parts.append(f"{pname}=...")
                    elif ptype == "BOOLEAN":
                        parts.append(f"{pname}=true/false")
                return ", ".join(parts)
        return "..."

    # Core
    lines.append("\nTemel:")
    core_tools = [
        "get_current_location", "open_app", "sys_info", "get_weather",
        "get_calendar_events", "add_calendar_event", "delete_calendar_event",
        "get_reminders", "add_reminder", "browser_control", "play_media",
        "shell_run", "set_volume", "analyze_screen", "get_youtube_channel_report",
        "save_memory", "delete_memory", "send_whatsapp_message",
        "save_whatsapp_contact", "browser_skill", "capture_camera",
    ]
    for t in core_tools:
        lines.append(_fmt(t))

    # System Health
    lines.append("\nSistem Sağlığı:")
    for t in ["get_system_health", "cleanup_temp_files", "cleanup_recycle_bin"]:
        lines.append(_fmt(t))

    # Process
    lines.append("\nSüreç Yönetimi:")
    for t in ["list_processes", "kill_process", "set_process_priority", "find_process_by_port"]:
        lines.append(_fmt(t))

    # File
    lines.append("\nDosya Yönetimi:")
    for t in ["find_large_files", "find_duplicate_files", "cleanup_folder", "get_folder_summary"]:
        lines.append(_fmt(t))

    # Network
    lines.append("\nAğ İzleme:")
    for t in ["get_network_summary", "list_net_connections", "ping_host"]:
        lines.append(_fmt(t))

    # Cron
    lines.append("\nZamanlanmış Görevler:")
    for t in ["add_cron_job", "list_cron_jobs", "remove_cron_job"]:
        lines.append(_fmt(t))

    # Services
    lines.append("\nServis Yönetimi:")
    for t in ["list_services", "control_service"]:
        lines.append(_fmt(t))

    lines.append("")
    lines.append("[FORMAT]")
    lines.append(
        'Araç çağrısı: arac_adi(parametre=\'değer\', parametre2=123)\n'
        'Parametre isimlerini Türkçe karakter kullanmadan yaz (location, app_name, query vb.).\n'
        "Örnek: get_weather(location='Ankara')  —  sys_info(query='time')  —  open_app(app_name='Spotify')"
    )
    return "\n".join(lines)
