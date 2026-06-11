# J.A.R.V.I.S — Sorun Giderme Kilavuzu

> Yaygin sorunlar, cozumler, hata kodlari ve debug ipuclari.

---

## Kurulum Sorunlari

### "pyaudio bulunamadi" Hatasi

**Hata**: `ModuleNotFoundError: No module named 'pyaudio'`

**Cozum**:
```bash
# Linux
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
pip install pyaudio
```

Eger hala calismazsa:
```bash
pip install pipwin
pipwin install pyaudio
```

### "faster-whisper model indirilemiyor" Hatasi

**Hata**: Model indirme sirasinda zaman asimi

**Cozum**:
1. Manuel indir:
```bash
# ~/.cache/faster_whisper/ klasorune indir
mkdir -p ~/.cache/faster_whisper/base
# Hugging Face'den model dosyalarini indir
```
2. VPN/proxy kullan
3. Daha kucuk model dene (`tiny`, `base`)

### "librnnoise.so bulunamadi" Hatasi

**Hata**: RNNoise kutuphanesi yuklenemiyor

**Cozum**:
```bash
python scripts/install_rnnoise.py
```

Bu betik basarisiz olursa:
1. `audio/lib/` klasorunu kontrol et
2. Kendin derle: `git clone https://github.com/GregorR/rnnoise-models.git`
3. Veya prebuilt binary indir: [rnnoise-models](https://github.com/GregorR/rnnoise-models/releases)

**Onemli**: RNNoise yoksa uygulama bypass modunda calisir (gurultu bastirmasiz).

---

## Backend Sorunlari

### Gemini API Baglanti Hatasi

**Hata**: `google.api_core.exceptions.PermissionDenied` veya `API key not valid`

**Cozum**:
1. `config/api_keys.json` dosyasinda API anahtarini kontrol et
2. Anahtar gecerli mi? [Google AI Studio](https://aistudio.google.com/)
3. Anahtarin Gemini API erisimi var mi?
4. Internet baglantini kontrol et
5. Turkiye'den erisim kisitli olabilir (VPN dene)

### Ollama Baglanti Hatasi

**Hata**: `httpx.ConnectError: [Errno 111] Connection refused`

**Cozum**:
1. Ollama calisiyor mu? `ollama list`
2. Ollama servisini baslat: `ollama serve`
3. Model indir: `ollama pull qwen2.5:1.5b`
4. Port 11434 acik mi? `curl http://localhost:11434/api/tags`
5. Baska bir servis portu kullaniyor mu?

### Ollama Model Yanit Vermiyor

**Hata**: LLM yanit uretmiyor veya cok yavas

**Cozum**:
1. Model dogru indirilmis mi? `ollama pull qwen2.5:1.5b`
2. RAM yeterli mi? 1.5B model ~3GB RAM gerektirir
3. CPU kullanimi kontrol et
4. Basit test: `ollama run qwen2.5:1.5b "Merhaba"`

---

## Ses Sorunlari

### Mikrofon Calismiyor

**Hata**: Ses algilanmiyor, VAD surekli sessiz

**Cozum**:
1. Mikrofon bagli mi? `arecord -l` (Linux)
2. Dogru mikrofon secili mi?
3. Ses seviyesi yeterli mi? `alsamixer` (Linux)
4. Baska uygulamada mikrofon calisiyor mu?
5. JARVIS debug log'u kontrol et: `cat logs/jarvis.log | grep -i "VAD\|RMS"`

### VAD Cok Hassas/Cok Duyarsiz

**Cozum**: `config/audio.yaml`'da `energy_threshold` degerini degistir:

```yaml
vad:
  fahrettin:
    energy_threshold: 30.0    # Daha hassas (dusuk sesleri algilar)
    # veya
    energy_threshold: 80.0    # Daha az hassas (sadece yuksek ses)
```

VAD debug log'u aktif et:
```yaml
vad:
  fahrettin:
    debug_log: true   # Her 50 frame'de RMS/threshold logla
```

### Wake Word Calismiyor

**Hata**: "Jarvis" dediginde tepki vermiyor

**Cozum**:
1. Wake word sadece Ollama modunda aktif
2. `config/wake_word.yaml`'da sensitivity ayarla:
   ```yaml
   openwakeword:
     sensitivity: 0.3  # Daha hassas (0.0-1.0)
   ```
3. openWakeWord kutuphanesi yuklu mu? `pip install openwakeword`
4. Alternatif: `energy` fallback'i dene (hic bagimlilik gerektirmez)

### TTS Ses Gelmiyor

**Hata**: JARVIS konusuyor ama ses duyulmuyor

**Cozum**:
1. Ses acik mi? UI'da mute butonunu kontrol et
2. Hoparlor calisiyor mu?
3. Piper modeli var mi? `ls voice/Fahrettin-TTS/`
4. Piper yuklu mu? `which piper` veya `pip list | grep piper`
5. Fallback zincirini kontrol et: `cat logs/jarvis.log | grep -i "TTS\|Piper\|edge"`

### RNNoise Gecikme Yapiyor

**Hata**: Ses gecikmeli geliyor

**Cozum**:
1. `config/audio.yaml`'da `enabled: false` yaparak gurultu bastirmayi kapat
2. Daha dusuk sample rate dene (16000 Hz)
3. CPU yukunu kontrol et

---

## UI Sorunlari

### Pencere Acilmiyor

**Hata**: `TclError: no display name and no $DISPLAY environment variable`

**Cozum**: Linux server'da SSH ile calisiyorsan X forwarding lazim:
```bash
ssh -X kullanici@sunucu
# veya
export DISPLAY=:0
```

### UI Cok Yavas

**Hata**: Arayuz kasilyor, animasyonlar akici degil

**Cozum**:
1. GPU hizlandirmasi kapali olabilir (Tkinter yazilimsal render)
2. Daha dusuk cozunurluk dene
3. Orb animasyonunu hafiflet
4. Diger uygulamalari kapat

### UI'da Turkce Karakter Bozuk

**Hata**: "Istanbul" yerine "I stanbul" veya "s" yerine "s" gibi

**Cozum**:
Bu normal — STT'den gelen metin `fix_turkish_syllable_split()` ile
duzeltilir. Sorun devam ederse:
1. `core/text_utils.py`'daki TURKISH_STOP listesini kontrol et
2. Eklemeli Turkce kelimeler icin ozel kural ekle

---

## Test Sorunlari

### Testler Calismiyor

**Hata**: `ModuleNotFoundError` test calistirirken

**Cozum**:
```bash
# Dogru Python yorumlayicisini kullan
.venv/bin/python3 -m unittest tests.test_smoke -v

# Degilse:
pip install -r requirements.txt
```

### Test Atlaniyor

**Hata**: Test `skipped` olarak isaretleniyor

**Sebep**:
1. pyaudio yok (sikca)
2. Ses donanimi yok
3. Belirli platform gerekiyor

**Cozum**: Atlanan testler genelde onemsizdir. Smoke test gecerse uygulama calisir.

---

## Genel Sorunlar

### "JARVIS yanit vermiyor"

**Cozum**:
1. Log kontrol: `cat logs/jarvis.log | tail -50`
2. UI durumuna bak (LISTENING mi? THINKING mi? ERROR mu?)
3. Mikrofon ve hoparloru kontrol et
4. Backend baglantisini kontrol et
5. `_is_speaking` kilidinde takili kalmissa yeniden baslat

### "Surekli ERROR durumunda"

**Cozum**:
```bash
# Loglari kontrol et
cat logs/jarvis.log | grep -i "ERROR\|CRITICAL\|Traceback" | tail -20
```

Yaygin nedenler:
1. API anahtari gecersiz
2. Ollama kapali
3. Ses cihazi kullanimda
4. Bellek yetersiz

### Ses Kaydediliyor Ama Transkripsiyon Gelmiyor

**Cozum**:
1. faster-whisper modeli indirilmis mi?
2. VAD esigi cok yuksek olabilir (`energy_threshold`)
3. STT engine dogru secilmis mi? (`config/audio.yaml` -> `stt.engine`)
4. Ses cok kisa olabilir (MIN_SILENCE_MS = 800ms)

---

## Debug Modu

### STT Debug

```bash
export JARVIS_DEBUG_STT=1
python main.py
```

Bu ortam degiskeni STT surecini detayli loglar.

### Log Seviyesi

Log seviyesi `logging.basicConfig(level=logging.DEBUG)` olarak ayarlidir.
Daha az log icin `WARNING` seviyesine cevirebilirsin:

```python
# main.py'de
logging.basicConfig(level=logging.WARNING)
```

### Thread Durumu

```bash
cat logs/jarvis.log | grep "ThreadName" | sort -u
```

Aktif thread'leri ve durumlarini gosterir.

--- 

## Iletisim

Sorun devam ederse:
1. `logs/jarvis.log` dosyasini incele
2. GitHub Issues sayfasina hata raporu olustur
3. Hata raporuna `logs/jarvis.log` ekle
