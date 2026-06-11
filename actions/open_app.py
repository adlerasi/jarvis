"""
Uygulama acma — Windows Start-Process / URI destegi ile calisir.
Alp Unlu tarafindan yapilmistir — @alppunlu
"""
from __future__ import annotations


import os

from actions.windows_utils import open_uri, open_windows_app


APP_ALIASES = {
    "edge":                "Microsoft Edge",
    "chrome":              "Google Chrome",
    "firefox":             "Firefox",
    "terminal":            "Terminal",
    "explorer":            "File Explorer",
    "spotify":             "Spotify",
    "vscode":              "Visual Studio Code",
    "vs code":             "Visual Studio Code",
    "code":                "Visual Studio Code",
    "notion":              "Notion",
    "slack":               "Slack",
    "discord":             "Discord",
    "whatsapp":            "WhatsApp",
    "telegram":            "Telegram",
    "zoom":                "zoom.us",
    "figma":               "Figma",
    "postman":             "Postman",
    "docker":              "Docker",
    "tableplus":           "TablePlus",
    "notepad":             "Notepad",
    "not defteri":         "Notepad",
    "cmd":                 "Command Prompt",
    "komut istemi":        "Command Prompt",
    "powershell":          "PowerShell",
    "calculator":          "Calculator",
    "hesap makinesi":      "Calculator",
    "paint":               "Paint",
    "mspaint":             "Paint",
    "task manager":        "Task Manager",
    "gorev yoneticisi":    "Task Manager",
    "control panel":       "Control Panel",
    "denetim masasi":      "Control Panel",
    "registry":            "Registry Editor",
    "regedit":             "Registry Editor",
    "mail":                "Mail",
    "eposta":              "Mail",
    "calendar":            "Calendar",
    "takvim":              "Calendar",
    "notes":               "Notes",
    "notlar":              "Notes",
    "music":               "Music",
    "muzik":               "Music",
    "photos":              "Photos",
    "fotograflar":         "Photos",
    "maps":                "Maps",
    "haritalar":           "Maps",
    "settings":            "Settings",
    "ayarlar":             "Settings",
    "camera":              "Camera",
    "kamera":              "Camera",
    "snipping tool":       "Snipping Tool",
    "ekran alintisi":      "Snipping Tool",
    "clock":               "Clock",
    "saat":                "Clock",
    "word":                "Microsoft Word",
    "excel":               "Microsoft Excel",
    "powerpoint":          "Microsoft PowerPoint",
    "teams":               "Microsoft Teams",
    "outlook":             "Microsoft Outlook",
    "onenote":             "Microsoft OneNote",
}


def open_app(app_name: str) -> str:
    """Uygulamayi acar, basari/hata mesaji dondurur."""
    if not app_name:
        return "Uygulama adi belirtilmedi."

    normalized = app_name.lower().strip()
    resolved   = APP_ALIASES.get(normalized, app_name)

    if os.name == "nt":
        ok, detail = open_windows_app(resolved)
        if ok:
            return detail
        ok, detail2 = open_uri(resolved)
        if ok:
            return f"{app_name} acildi."
        return detail or detail2

    return f"'{app_name}' desteklenen platformda calismiyor."
