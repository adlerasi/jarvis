# J.A.R.V.I.S — Guvenlik Modeli

> Shell komut filtreleme, input validasyonu, API anahtar yonetimi, thread safety.

---

## 1. Shell Komut Guvenligi (`actions/shell.py`)

### Bloke Edilen Komutlar

```python
BLOCKED_PREFIXES = [
    "rm", "sudo", "mkfs", "dd", "shutdown", "reboot",
    "init", "poweroff", "halt", ":(){", "diskutil",
    "mv /", "chmod 777 /"
]
```

Her komut calistirilmadan once:
1. normalize edilir (lowercase + trim)
2. BLOCKED_PREFIXES ile karsilastirilir
3. Bloklanirsa -> guvenlik uyarisi gonderilir
4. Gecerse -> `subprocess.run(timeout=30)` ile calistirilir

### Timeout Guvenligi

Tum shell komutlari 30 saniye timeout ile sinirlidir. Asiminda `TimeoutExpired` hatasi firlatilir.

---

## 2. Input Validasyonu

| Kural | Limit | Uygulandigi Yer |
|-------|-------|-----------------|
| STT text cap | 10,000 karakter | `_on_text_command()` |
| Tool call arg cap | 500 karakter/arg | `parse_local_tool_call()` |
| Tool call total cap | 2,000 karakter | `parse_local_tool_call()` |
| Tool name whitelist | Sadece kayitli araclar | `VALID_TOOLS` seti |

### Tool Name Whitelist

ToolRegistry'de kayitli olmayan hicbir arac ismi kabul edilmez. Bilinmeyen arac adi `None` doner, islem yapilmaz.

### Tool Call Parsing

```python
def parse_local_tool_call(text: str) -> dict | None:
    # 1. Toplam uzunluk kontrolu (>2000 -> None)
    # 2. Regex ile tool adi + args ayikla
    # 3. Tool adi VALID_TOOLS icinde mi?
    # 4. Her arg degeri >500 karakter -> None
    # 5. JSON parse -> dict
```

---

## 3. API Anahtar Yonetimi

### Koruma

- API anahtarlari `config/api_keys.json` dosyasinda
- Dosya `.gitignore` ile korunuyor
- `config/api_keys.example.json` sadece ornek

### Gereksinim

```json
{
  "gemini_api_key": "AIzaSy..."  // ZORUNLU (Gemini modu icin)
}
```

### Gemini Modu Kontrolu

`has_gemini_api_key()` fonksiyonu API anahtarinin varligini kontrol eder. Anahtar yoksa Gemini modu kullanilamaz.

---

## 4. Platform Guvenligi

### OS Detection

`GeminiProvider.build_config()` sistem prompt'una `[SISTEM BILGISI]` enjekte eder:

```
[SISTEM BILGISI]
Isletim Sistemi: Windows 10
Shell: powershell.exe
Yol ayraci: \
```

AI'nin yanlis platform komutu uretmesini engeller.

### Platform Ayrimi

Zararli olabilecek komutlar platforma gore ayrilmistir:

```python
if IS_WINDOWS:
    # Windows spesifik kod (powershell, start, nircmd)
elif IS_MACOS:
    # macOS spesifik kod (osascript, open)
else:
    # Linux spesifik kod (pactl, xdg-open)
```

- Windows'ta `rm -rf /` gibi UNIX komutlari calismaz
- macOS'ta Windows registry kodlari calismaz

---

## 5. Kullanici Inisiyatifi Guvenligi (`_user_initiated` Gate)

AI'nin izinsiz eylem yapmasini engeller:

```python
_user_initiated = False  # Baslangicta False

def _on_text_command(self, text):
    self._user_initiated = True  # Kullanici konusunca True
    ...

def _handle_browser_control(self, args, loop):
    if not self._user_initiated:
        return "HATA: Kullanici etkilesimi olmadan bu islem yapilamaz."
    ...
```

Sadece tarayici kontrolu gibi yan etkili tool'larda kullanilir. Basit sorgularda (hava durumu, zaman) kontrol yoktur.

---

## 6. Exception Logging

Gizli hatalari engellemek icin:

```python
# DOGRU
try:
    sonuc = riskli_islem()
except Exception:
    traceback.print_exc()  # Log'a yaz, sessizce gecme

# ISTISNA 1: NDJSON stream parser
#   - Kismi/eksik JSON beklenir
#   - Her chunk loglamak flood yaratir

# ISTISNA 2: Best-effort fallback
#   - windows_utils, process_manager, youtube_stats
#   - Dis cagirici zaten logluyor

# ISTISNA 3: cleanup finally blogu
#   - close()/terminate()/kill()
#   - traceback.print_exc() ILE loglanir
```

---

## 7. Thread Safety

| Modul | Korumali Alan | Kilit |
|-------|--------------|-------|
| `main.py` | `_is_speaking` | `_speaking_lock` (Lock) |
| `core/skill_manager.py` | Skills listesi, watcher state | `_lock` (RLock) |
| `ui/sound_manager.py` | Sound procs, ambient/foreground | `_lock` (RLock) |
| `actions/watchdog/file_watcher.py` | Debounce timer, event queue | `_debounce_lock`, `_history_lock` |
| `actions/system_cron.py` | NetworkAnomalyDetector.scan() | `_nad_lock` (Lock) |
| `actions/cron_web_ui.py` | `_running` flag | Yok (min race, benign) |

---

## 8. Sistem Prompt Guvenligi

System prompt (`core/prompt.txt`) sunlari icerir:

- Tool kullanim kurallari
- Guvenlik kisitlamalari
- Platform bilgisi
- Dil tercihleri

Prompt'ta `[CONTEXT]` ve `[MEMORY]` placeholder'lari calisma zamaninda
doldurulur. Bu sayede AI her zaman guncel baglam ve bellege sahip olur.

---

## 9. Bagimlilik Guvenligi

### Guvenilmeyen Kaynaklar

- **Selenium WebDriver**: WhatsApp modulu icin harici browser kontrolu
- **subprocess**: Shell komutlari, Piper TTS, edge-tts
- **HTTP/S**: Gemini API, Ollama, wttr.in, YouTube API

### Ozel Dikkat Gerektiren Moduller

| Modul | Risk | Onlem |
|-------|------|-------|
| `actions/shell.py` | Komut enjeksiyonu | Prefix blacklist + timeout |
| `actions/browser.py` | URL enjeksiyonu | `webbrowser.open` (guvenli) |
| `actions/whatsapp.py` | Selenium WebDriver | Kullanici inisiyatifi kontrolu |
| `core/ollama_provider.py` | HTTP API | Sadece localhost:11434 |
| `memory/memory_manager.py` | JSON dosya yazma | Input dogrulama yok (AI-generated) |

---

## 10. Hatirlatmalar

Guvenlikle ilgili temel prensipler:

1. **API anahtarlarini asla commit etme** - `.gitignore` kullan
2. **Shell komutlarinda whitelist kullan, blacklist degil** - mevcut blacklist yetersiz, whitelist planlaniyor
3. **Tum dis kaynaklari dogrula** - tool call arg'lari, URL'ler
4. **Thread race condition'larina dikkat et** - paylasilan durumu kilitlerle koru
5. **Hatalari gizleme** - her `except` bir `traceback.print_exc()` gerektirir
