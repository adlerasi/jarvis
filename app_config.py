# Alp Ünlü tarafından yapılmıştır — @alppunlu
from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "api_keys.json"


DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
    "backend_type": "gemini",
    "ollama_model": "",
    "ollama_tts_voice": "piper-fahrettin",   # default local Piper voice
}


def get_ollama_tts_voices() -> list[dict]:
    """Return available TTS voice options for Ollama (local) mode."""
    import subprocess
    voices = []

    # ── Piper – Fahrettin (yerel, offline) ───────────────────────────────────
    base = Path(__file__).resolve().parent
    fahrettin_onnx = base / "voice" / "Fahrettin-TTS" / "tr_TR-fahrettin-medium.onnx"
    if fahrettin_onnx.exists():
        voices.append({
            "id": "piper-fahrettin",
            "label": "Piper – Fahrettin (Yerel · Türkçe)",
        })

    # ── edge-tts – Microsoft Neural voices (internet gerektirir) ────────────
    try:
        r = subprocess.run(
            ["edge-tts", "--list-voices"],
            capture_output=True, text=True, timeout=6
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("tr-TR-AhmetNeural"):
                    voices.append({"id": "edge-ahmet", "label": "Edge – Ahmet Neural (Türkçe Erkek)"})
                elif line.startswith("tr-TR-EmelNeural"):
                    voices.append({"id": "edge-emel",  "label": "Edge – Emel Neural (Türkçe Kadın)"})
    except Exception as e:
        print(f"[App Config] Error fetching edge-tts voices: {e}")

    # ── spd-say fallback (her zaman dahil et) ────────────────────────────────
    voices.append({"id": "spd-say", "label": "spd-say (Sistem Sesi)"})

    return voices


def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config.update(raw)
    except Exception as e:
        print(f"[App Config] Error loading config (using defaults): {e}")
    return config


def save_app_config(updates: dict) -> dict:
    config = load_app_config()
    for key, value in (updates or {}).items():
        if value is None:
            continue
        config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_app_config_value(key: str, default=None):
    return load_app_config().get(key, default)


def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    return bool(value)


def get_ollama_models() -> list[str]:
    import urllib.request
    try:
        url = "http://localhost:11434/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = data.get("models", [])
            return [m["name"] for m in models if "name" in m]
    except Exception as e:
        print(f"[App Config] Error fetching Ollama models: {e}")
        return []
