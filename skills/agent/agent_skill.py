"""Agent Skill - ACA istekleri icin dogal dil arayuzu."""

from __future__ import annotations
import re
from typing import Any

SKILL_ID = "agent-v1"
SKILL_NAME = "Otonom Ajan"

# JARVIS tarafindan startup'ta set edilir
_agent_manager: Any = None


def set_agent_manager(mgr: Any) -> None:
    global _agent_manager
    _agent_manager = mgr


ACTIONS: dict[str, list[str]] = {
    "execute_goal": [
        r"(?:yap|gerceklestir|gerçekleştir|hallet|otomatik|kendi.*?yap|ajan.*?yap|asistan.*?yap)",
        r"(?:aca|ajan|agent).*?(?:baslat|başlat|calistir|çalıştır|etkinlestir|etkinleştir)",
        r"(?:otonom|kendi kendine).*?(?:calis|çalış|yap|hallet|isle|işle)",
        r"\b(?:oluştur|olustur|bul|indir|getir|gönder|gonder|ara|temizle|kaydet|sil|oku|yaz|aç|ac|kapat|düzenle|duzenle|karşılaştır|karsılastır|kopyala|taşı|tasi|baslat|başlat|durdur)\b",
    ],
    "get_status": [
        r"(?:durum|status|ilerleme|ne yapıyor|ne yapiyor|ne durumda)",
        r"(?:aca).*?(?:durum|ne yapiyor|ne yapıyor)",
        r"(?:ajan).*?(?:durumu|durum)",
    ],
    "cancel_goal": [
        r"(?:dur|durdur|iptal|kapat|kes|sonlandır|sonlandir)",
        r"(?:aca).*?(?:dur|durdur|iptal|kapat)",
    ],
    "approve_step": [
        r"(?:onayla|onaylıyorum|onayliyorum|devam|evet|tamam|olur|yap)",
        r"(?:adim|adım).*?(?:onayla|onay|devam)",
    ],
    "reject_step": [
        r"(?:reddet|red|hayır|hayir|yapma|dur|iptal et)",
        r"(?:adim|adım).*?(?:reddet|red|hayır|hayir)",
    ],
}


def classify_agent_intent(text: str) -> str:
    text_lower = text.lower().strip()
    for action, patterns in ACTIONS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return action
    return "none"


def _extract_goal(text: str) -> str:
    triggers = [
        r"^(?:yap|gerceklestir|gerçekleştir|hallet|otomatik|ajan|aca)\s+",
        r"^(?:kendi kendine|otonom)\s+",
    ]
    cleaned = text
    for pat in triggers:
        cleaned = re.sub(pat, "", cleaned, count=1)
    cleaned = cleaned.strip().rstrip(".!")
    return cleaned


def route_agent_request(user_text: str) -> str | None:
    """SkillEngine uyumlu route (str -> str | None)."""
    action = classify_agent_intent(user_text)
    if action == "none":
        return None

    mgr = _agent_manager
    if mgr is None:
        return "ACA sistemi henuz baslatilmadi."

    if action == "execute_goal":
        goal = _extract_goal(user_text)
        if not goal:
            return "Ne yapmami istedigini anlamadim. Ornek: 'Masaustunde deneme.txt olustur'"
        return mgr.execute_goal(goal)

    if action == "get_status":
        status = mgr.get_goal_status()
        if not status:
            return "Su an calisan bir hedef yok."
        return (
            f"Durum: {status.get('status', '?')}\n"
            f"Hedef: {status.get('goal_text', '?')}\n"
            f"Adim: {status.get('completed_steps', 0)}/{status.get('total_steps', 0)}\n"
            f"Basarisiz: {status.get('failed_steps', 0)}"
        )

    if action == "cancel_goal":
        result = mgr.cancel_goal()
        if result:
            return "Hedef iptal edildi."
        return "Calisan hedef yok veya iptal edilemedi."

    if action == "approve_step":
        mgr.approve_current_step()
        return "Adim onaylandi, devam ediliyor."

    if action == "reject_step":
        mgr.reject_current_step()
        return "Adim reddedildi."

    return None
