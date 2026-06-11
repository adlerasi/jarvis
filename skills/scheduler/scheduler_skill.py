"""
Scheduler Skill — Zamanlanmış görev yönetimi (Cron).
"""

from __future__ import annotations
import re
from actions.system_cron import add_cron_job, list_cron_jobs, remove_cron_job

SKILL_ID = "scheduler-v1"
SKILL_NAME = "Zamanlayici"

# ── Trigger patterns ──────────────────────────────────────────────────────
# ASCII fallback: tüm Türkçe karakterler için (ş→s, ç→c, ü→u, ö→o, ğ→g, ı→i)
TRIGGERS = {
    "list_jobs": [
        r"(?:zamanlanmis|zamanlanmış|zamanli|zamanlı|cron|gorev|görev|task|is|iş|otomasyon|planli|planlı).*?(?:neler|ne var|listele|goster|göster|bak|gor|gör|soyle|söyle|yaz|dok|dök)",
        r"(?:gorevlerim|görevlerim|tasklarim|joblar|islerim|planlarım|planlarim).*?(?:neler|ne var|listele|goster|göster)",
        r"(?:tum|tüm|butun|bütün|aktif|pasif|calisan|çalışan|durmus|durmuş|aktif olan).*?(?:gorev|görev|task|zamanlanmis|zamanlanmış|is|iş)",
        r"(?:cron).*?(?:listele|goster|göster|neler|ne var|jobs|joblar|göster)",
        r"(?:planli|planlı).*?(?:gorev|görev|is|iş).*?(?:neler|listele|goster|göster)",
        r"(?:scheduled|schedule|scheduled task).*?(?:listele|goster|göster|neler|ne var)",
    ],
    "add_job": [
        r"(?:yeni|bir tane|tane|yenisini).*?(?:gorev|görev|task|zamanlanmis|zamanlanmış|is|iş|planli|planlı|cron).*?(?:ekle|olustur|oluştur|kur|ayarla|baslat|başlat|tanimla|tanımla)",
        r"(?:her|her gün|her gun|her hafta|her ay|saat başı|saat basi|gunluk|günlük|haftalik|haftalık|aylik|aylık|yıllık|yillik|periyodik).*?(?:gorev|görev|task|is|iş|calistir|çalıştır|yap|koş|kos|baslat|başlat)",
        r"(?:gorev|görev|task|is|iş).*?(?:ekle|olustur|oluştur|kur|ayarla|tanimla|tanımla|planla)",
        r"(?:hatirlat|hatırlat|animsat|anımsat|rapor|bildir|uyar).*?(?:ekle|kur|ayarla|zamanla|planla|oluştur|olustur)",
        r"(?:otomatik).*?(?:gorev|görev|is|iş|calistir|çalıştır|yap).*?(?:ekle|kur|ayarla|olustur|oluştur)",
        r"(?:her).*?(?:dakika|saat|gun|gün|hafta|ay).*?(?:basi|başı|bir).*?(?:calistir|çalıştır|yap|calissin|çalışsın)",
    ],
    "remove_job": [
        r"(?:gorev|görev|task|zamanlanmis|zamanlanmış|is|iş|cron|job).*?(?:sil|kaldir|kaldır|cikar|çıkar|iptal|durdur|bitir|kaldır)",
        r"(?:cron|zamanlayici|zamanlayıcı|job).*?(?:sil|kaldir|kaldır|cikar|çıkar|iptal|durdur)",
        r"(?:sil|iptal|durdur|kaldir|kaldır).*?(?:gorevi|görevi|taski|jobı|jobu|zamanlanmışı|zamanlanmisi)",
        r"(?:numarali).*?(?:gorev|görev|task|job).*?(?:sil|iptal|durdur|kaldir|kaldır)",
        r"(?:kaldır|kaldir|sil).*?(?:görevi|gorevi|taski)",
    ],
}


def _parse_schedule(text: str) -> tuple[str, str]:
    """Metinden schedule type ve value çıkarma."""
    text_lower = text.lower()

    # Interval (saniye)
    interval_match = re.search(r'(\d+)\s*(?:saniye|dakika|saat|gun|gün)', text_lower)
    if interval_match:
        value = int(interval_match.group(1))
        unit_slice = text_lower[interval_match.start():interval_match.end()]
        if "dakika" in unit_slice:
            value *= 60
        elif "saat" in unit_slice:
            value *= 3600
        elif "gun" in unit_slice or "gün" in unit_slice:
            value *= 86400
        return "interval", str(value)

    # Günlük (saat)
    daily_match = re.search(r'(?:her\s+gun|gün|gunluk|günlük).*?(?:saat)?\s*(\d{1,2}):(\d{2})', text_lower)
    if daily_match or "her gun" in text_lower or "her gün" in text_lower or "gunluk" in text_lower or "günlük" in text_lower:
        hour = daily_match.group(1) if daily_match else "08"
        minute = daily_match.group(2) if daily_match else "00"
        return "daily", f"{int(hour):02d}:{int(minute):02d}"

    # Haftalık
    if "her hafta" in text_lower or "haftalik" in text_lower or "haftalık" in text_lower:
        return "weekly", "0-08:00"

    # Bir kere
    if "bir kere" in text_lower or "tek seferlik" in text_lower or "sadece bir" in text_lower:
        return "once", "2026-06-07T12:00"

    return "daily", "08:00"


def _extract_job_name(text: str) -> str:
    """Görev adı çıkarma."""
    text_lower = text.lower()

    # "gorev X ekle" -> X
    match = re.search(r'(?:gorev|görev|task)\s+(.+?)\s+(?:ekle|olustur|oluştur|kur)', text_lower)
    if match:
        return match.group(1).strip().capitalize()

    # "X gorevi ekle" -> X (Turkish accusative suffix)
    match = re.search(r'(.+?)\s+(?:gorev|görev|task)\w*\s+(?:ekle|olustur|oluştur|kur)', text_lower)
    if match:
        return match.group(1).strip().capitalize()

    # "X ekle gorev" -> X
    match = re.search(r'(.+?)\s+(?:ekle|olustur|oluştur|kur)\s+(?:gorev|görev|task)', text_lower)
    if match:
        return match.group(1).strip().capitalize()

    return "Yeni Gorev"


def _extract_command(text: str) -> str:
    """Görev komutu çıkarma."""
    text_lower = text.lower()

    if any(w in text_lower for w in ["temp", "gecici", "geçici", "cache"]):
        return "temp_cleanup"
    elif any(w in text_lower for w in ["saglik", "sağlık", "health", "kontrol"]):
        return "health_check"
    elif any(w in text_lower for w in ["sistem", "sys info", "bilgi"]):
        return "sys_info"
    elif any(w in text_lower for w in ["recycle", "cop", "çöp", "geri donusum", "geri dönüşüm"]):
        return "recycle_cleanup"

    return "health_check"


def classify_scheduler_intent(text: str) -> tuple[str, dict]:
    """Kullanıcı metninden scheduler intent'ini çıkarır."""
    text_lower = text.lower().strip()

    # 1. Silme
    for pattern in TRIGGERS["remove_job"]:
        if re.search(pattern, text_lower):
            id_match = re.search(r'(\d+)', text_lower)
            if id_match:
                return "remove_job", {"job_id": int(id_match.group(1))}
            return "remove_job", {"job_id": 0}

    # 2. Ekleme
    for pattern in TRIGGERS["add_job"]:
        if re.search(pattern, text_lower):
            name = _extract_job_name(text)
            command = _extract_command(text)
            schedule_type, schedule_value = _parse_schedule(text)
            return "add_job", {
                "name": name,
                "command": command,
                "schedule_type": schedule_type,
                "schedule_value": schedule_value
            }

    # 3. Listeleme
    for pattern in TRIGGERS["list_jobs"]:
        if re.search(pattern, text_lower):
            return "list_jobs", {"enabled_only": False}

    # Fallback keyword
    scheduler_keywords = ["gorev", "görev", "task", "zamanlanmis", "zamanlanmış",
                          "cron", "zamanlayici", "zamanlayıcı", "hatirlat", "hatırlat",
                          "rapor", "schedule"]
    if any(kw in text_lower for kw in scheduler_keywords):
        return "list_jobs", {"enabled_only": False}

    return "none", {}


def execute_scheduler_skill(action: str, params: dict) -> str:
    """Scheduler skill çalıştırıcı."""
    if action == "list_jobs":
        return list_cron_jobs(params.get("enabled_only", False))
    elif action == "add_job":
        return add_cron_job(
            params.get("name", ""),
            params.get("command", ""),
            params.get("schedule_type", ""),
            params.get("schedule_value", ""))
    elif action == "remove_job":
        return remove_cron_job(params.get("job_id", 0))
    return f"Bilinmeyen scheduler action: {action}"


def route_scheduler_request(user_text: str) -> str | None:
    """Kullanıcı metnini analiz eder, scheduler skill'i ile eşleşirse çalıştırır."""
    intent, params = classify_scheduler_intent(user_text)
    if intent == "none":
        return None

    result = execute_scheduler_skill(intent, params)
    return result
