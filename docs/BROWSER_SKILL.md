# Tarayıcı Yönetimi (Browser Skill)

## Kullanılan Teknoloji

- **Birincil:** Python `webbrowser` modülü (platformun varsayılan tarayıcısını açar)
- **Skill:** `skills/browser/browser_skill.py` — regex eşleşme ile doğrudan routing
- **Action:** `actions/browser.py` — AI tool çağrısı ile tarayıcı kontrolü
- **Güvenlik:** `_user_initiated` gate — AI izinsiz tarayıcı açamaz

## Yetenekler Listesi

| Yetenek | Skill | Action | Açıklama |
|---------|-------|--------|----------|
| URL aç | ✅ | ✅ | Bilinen site veya özel URL |
| Google arama | ✅ | ✅ | Sorgu ile arama |
| YouTube oynatma | ✅ | ✅ | Video/kanal arama ve oynatma |
| Bilinen site kısayolları | ✅ | ✅ | youtube.com, github.com, gmail.com |
| Özel URL | ❌ | ✅ | Kullanıcının verdiği herhangi bir URL |

### Browser Skill (`skills/browser/browser_skill.py`)

```python
def route_browser_request(user_text: str) -> str | None:
    """
    Kullanıcı metnini browser skill desenleriyle eşleştirir.
    Eşleşme varsa skill'i çalıştırır, sonucu döner.
    """
    _load_triggers()
    text = user_text.strip()
    
    # Regex desenleriyle eşleştir
    for compiled, action, raw_pattern in _TRIGGER_PATTERNS:
        m = compiled.search(text)
        if m:
            captured = m.group(1).strip()
            if action == "open_url":
                known_sites = {
                    "youtube": "https://youtube.com",
                    "google": "https://google.com",
                    "github": "https://github.com",
                    "gmail": "https://mail.google.com",
                }
                if " " in captured and captured.lower() not in known_sites:
                    return None  # çok kelimeli → skill değil
                url = known_sites.get(captured.lower(), f"https://{captured}.com")
                return execute_browser_skill("open_url", url=url)
            elif action == "search":
                return execute_browser_skill("search", query=captured)
            elif action == "play_youtube":
                return execute_browser_skill("play_youtube", query=captured)
    return None
```

### Browser Action (`actions/browser.py`)

```python
# actions/browser.py — AI tarafından çağrılan browser fonksiyonları
def browser_control(action: str, url: str | None = None, query: str | None = None) -> str:
    """Tarayıcı kontrol fonksiyonu."""
    try:
        if action == "open_url":
            if url:
                webbrowser.open(url)
                return f"{url} açılıyor..."
            return "URL belirtilmedi."
        elif action == "search":
            if query:
                webbrowser.open(f"https://www.google.com/search?q={quote(query)}")
                return f"Google'da '{query}' aranıyor..."
            return "Arama sorgusu belirtilmedi."
        elif action == "play_youtube":
            if query:
                webbrowser.open(f"https://www.youtube.com/results?search_query={quote(query)}")
                return f"YouTube'da '{query}' aranıyor..."
            return "YouTube sorgusu belirtilmedi."
        return f"Bilinmeyen browser action: {action}"
    except Exception:
        traceback.print_exc()
        return "Tarayıcı işlemi başarısız."
```

## Trigger Pattern'leri (`triggers.json`)

```json
{
  "triggers": {
    "patterns": [
      "(?:ac|aç|open|git)\\s*(?:bana)?\\s*(youtube)",
      "(?:ac|aç|open|git)\\s*(?:bana)?\\s*(google)",
      "(?:ac|aç|open|git)\\s*(?:bana)?\\s*(github)",
      "(?:ac|aç|open)\\s*(?:bana)?\\s*(gmail)",
      "google(?:dan)?\\s+(?:ara|da ara|de ara|a)?\\s*(.+?)(?:\\?*)$",
      "google(?:da|de)?\\s+ara\\s*(.+?)$",
      "youtube(?:dan)?\\s+(?:ac|aç|ara|da ara|de ara|a)?\\s*(.+?)$"
    ]
  }
}
```

Türkçe karakter desteği için ASCII fallback: `(?:ac|aç)` — her iki yazım da eşleşir.

## Güvenlik Modeli

```python
# main.py — AI'nın izinsiz tarayıcı açmasını engeller
_user_initiated = False  # Kullanıcı ilk mesajı gönderene kadar False

async def _handle_browser_control(self, args, loop) -> str:
    """Browser control handler — kullanıcı onayı gerektirir."""
    if not self._user_initiated:
        return ("Güvenlik: Tarayıcı kontrolü için önce bir mesaj göndermelisiniz. "
                "AI doğrudan tarayıcı açamaz.")
    
    action = args.get("action", "")
    url = args.get("url")
    query = args.get("query")
    
    return await loop.run_in_executor(
        None, lambda: browser_control(action, url=url, query=query)
    )
```

**- `_user_initiated` güvenlik gate**: AI (Gemini/Ollama) `browser_control` tool'unu çağıramaz. Kullanıcı önce bir mesaj göndermelidir.
- **Skill routing**: Browser skill (AI'sız) sadece kullanıcı metnini eşleştirir — AI bu yolu kullanamaz.

## Session & Cookie Yönetimi

JARVIS tarayıcı session/cookie yönetimi yapmaz:
- Varsayılan tarayıcı açılır (mevcut session'ı kullanır)
- YouTube/WhatsApp gibi servisler için kullanıcının tarayıcıda oturum açmış olması gerekir
- WhatsApp skill: Selenium WebDriver ile ayrı bir browser instance'ı açar (kendi session'ı var)

## Kod Akışı

```
Kullanıcı: "youtube aç"
    │
    ├── SkillManager.route("youtube aç")
    │       │
    │       ├── triggers.json pattern eşleşmesi
    │       │   r"(?:ac|aç|open|git)\s*(?:bana)?\s*(youtube)"
    │       │   → captured = "youtube"
    │       │
    │       ├── action = "open_url"
    │       ├── url = "https://youtube.com"
    │       ├── execute_browser_skill("open_url", url="https://youtube.com")
    │       │       └── browser_control("open_url", url="https://youtube.com")
    │       │               └── webbrowser.open("https://youtube.com")
    │       └── return "youtube açılıyor..."
    │
    └── UI'da göster → LLM'e gidilmez

Alternatif: AI tool çağrısı ile
    LLM: browser_control(action="open_url", url="https://example.com")
    │
    ├── _handle_browser_control()
    │       ├── _user_initiated kontrolü
    │       └── browser_control() → webbrowser.open()
    └── Sonuç LLM'e döner
```

## Kullanım Örnekleri

| Komut | Skill/Action | Sonuç |
|-------|-------------|-------|
| "youtube aç" | Skill | youtube.com açar |
| "google'da ara yapay zeka" | Skill | Google arama sayfası |
| "github aç" | Skill | github.com açar |
| "bana stackoverflow aç" | Skill | stackoverflow.com açar |
| "AI tarayıcıda şu siteyi aç" | Action (AI) | _user_initiated kontrolü → açar |
| "siteye git python.org" | Skill | python.org açar |

[Bkz. SKILLS.md](SKILLS.md) | [Bkz. AGENTS.md](AGENTS.md) | [Bkz. ORCHESTRATOR.md](ORCHESTRATOR.md)
