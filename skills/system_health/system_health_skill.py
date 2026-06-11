"""
System Health Skill - Sistem sağlık kontrolü
"""

from __future__ import annotations
import re
from actions.system_doctor import get_system_health, cleanup_temp_files, cleanup_recycle_bin

SKILL_ID = "system-health-v1"
SKILL_NAME = "Sistem Sağlık"

TRIGGERS = {
    "health_check": [
        r"(?:bilgisayar|sistem|pc|laptop|makina|makine|pc'm|pc'im|bilgisayarım|bilgisayarim).*?(?:durum|nasıl|nasil|kontrol|rapor|sağlık|saglik|sağlıklı|saglikli|performans|iyi|kötü|kotu)",
        r"(?:cpu|ram|disk|bellek|islemci|işlemci|harddisk|ssd|ekran karti|ekran kartı).*?(?:kullanım|kullanim|doluluk|yuzde|yüzde|durum|oran|ne kadar|kaç|kac)",
        r"(?:performans|hız|hiz|yavaş|yavas|kasma|takilma|takılma|donma|cok yavas|çok yavaş|çok yavaş|yavaşlık|yavaslik).*?(?:neden|sebep|kontrol|cozum|çözüm|nedir)",
        r"(?:sıcaklık|sicaklik|isi|ısı|heat|fan|fan hızı|fan hizi|sogutma|soğutma|sıcak|sicak).*?(?:durum|kontrol|kac|kaç|normal|yuksek|yüksek|tehlikeli)",
        r"(?:ne kadar).*?(?:ram|cpu|disk|bellek|islemci|işlemci|bellek|depolama)",
        r"(?:genel|full|tüm|tum|butun|bütün|tum).*?(?:durum|rapor|ozet|özet|kontrol|bilgi|analiz)",
        r"(?:sistem).*?(?:bilgi|rapor|ozeti|özeti|analiz|ozellik|özellik|donanım|donanim|konfigurasyon|konfigürasyon)",
        r"(?:windows|isletim|işletim|os).*?(?:surum|sürüm|versiyon|guncel|güncel|guncelleme|güncelleme)",
        r"(?:bellek|ram).*?(?:ne kadar|kac|kaç|dolu|bos|boş|yeterli|yetmez)",
        r"(?:disk|depolama|ssd|harddisk|hdd).*?(?:dolu|bos|boş|kalmış|kalmis|kac|kaç|gb|tb)",
        r"(?:yavaş|yavas|kas|don|yavaşlama|yavaslama).*?(?:bilgisayar|pc|sistem|laptop|makina|makine)",
    ],
    "cleanup_temp": [
        r"(?:temp|geçici|gecici|gereksiz).*?(?:temizle|sil|temizlik|yap|bosalt|boşalt|kaldir|kaldır)",
        r"(?:disk|yer|alan|depolama).*?(?:temizle|bosalt|boşalt|ac|aç|yer ac|yer aç|alan ac|alan aç)",
        r"(?:cache|önbellek|onbellek|gecici dosya|geçici dosya).*?(?:temizle|sil|yok et|bosalt|boşalt)",
        r"(?:cop|cöp|çöp|recycle).*?(?:temizle|sil)",
        r"(?:temizlik|sil).*?(?:temp|gecici|geçici|cache|dosya)",
        r"(?:gerekisiz|gereksiz).*?(?:dosya|dosyalar|veri).*?(?:temizle|sil)",
    ],
    "cleanup_recycle": [
        r"(?:çöp kutusu|cop kutusu|recycle bin|geridonusum|geri dönüşüm|geri donusum|cop kutusu).*?(?:bosalt|boşalt|temizle|sil|yap)",
        r"(?:cop|cöp|cöp|çöp).*?(?:kutusu).*?(?:bosalt|boşalt|temizle|sil|yap)",
        r"(?:bosalt|boşalt|temizle).*?(?:cop|cöp|çöp|recycle)",
        r"(?:çöp|cop).*?(?:kutusu).*?(?:doldu|dolu|dolmuş|dolmus|bostalt|boşalt)",
    ],
}


def classify_system_health_intent(text: str) -> tuple[str, str]:
    """Kullanıcı metninden sistem sağlık intent'ini çıkarır."""
    text_lower = text.lower().strip()

    # Hava durumu sorgularını engelle (weather'a gitsin)
    if "hava" in text_lower:
        return "none", ""

    for intent, patterns in TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent, ""

    # Fallback keyword
    keywords = {
        "health_check": ["sağlık", "saglik", "durum", "cpu", "ram", "disk", "sıcaklık", "sicaklik", "isi", "ısı", "yavaş", "yavas", "kas"],
        "cleanup_temp": ["temp", "geçici", "gecici", "cache", "önbellek", "onbellek"],
        "cleanup_recycle": ["çöp", "cop", "recycle", "geri dönüşüm", "geri donusum"],
    }

    for intent, words in keywords.items():
        if any(w in text_lower for w in words):
            return intent, ""

    return "none", ""


def execute_system_health_skill(action: str, query: str = "all") -> str:
    """System health skill çalıştırıcı."""
    if action == "health_check":
        return get_system_health(query)
    elif action == "cleanup_temp":
        return cleanup_temp_files()
    elif action == "cleanup_recycle":
        return cleanup_recycle_bin()
    return f"Bilinmeyen sistem action: {action}"


def route_system_health_request(user_text: str) -> str | None:
    """Kullanıcı metnini analiz eder, sistem sağlık skill'i ile eşleşirse çalıştırır."""
    intent, _ = classify_system_health_intent(user_text)
    if intent == "none":
        return None

    result = execute_system_health_skill(intent)
    return result
