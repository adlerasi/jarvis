# Quickstart: Orkestrasyon Onarımı Doğrulama

**Phase 1 — Doğrulama Senaryoları**

---

## Önkoşullar

```bash
# Sanal ortam aktif
source .venv/bin/activate

# Tüm mevcut testler geçiyor mu?
python -m unittest discover tests -v
# Beklenen: 2803+ pass, 2 skip, 0 fail
```

---

## Faz 1 Doğrulama (Thread Safety + RNNoise + Dual STT + Provider Interface)

### 1. Thread Safety — safe_call Test
```python
# tests/test_smoke.py'ye eklenecek (veya yeni test_ui_thread.py)
def test_safe_call_bg_thread_no_crash(self):
    """safe_call background thread'den çağrıldığında exception fırlatmamalı."""
    import threading
    errors = []
    def bg():
        try:
            # create minimal ui or use mock
            pass
        except Exception as e:
            errors.append(e)
    t = threading.Thread(target=bg)
    t.start()
    t.join(timeout=2)
    self.assertEqual(errors, [])
```

### 2. RNNoise Integration
```bash
# Manuel smoke test (sudo gerekebilir):
sudo -E python main.py
# Beklenen: "[Ollama] RNNoise aktif" log'u
# Beklenen: STT çalışıyor (sesli komut: "merhaba")
```

### 3. Provider Interface (send_text standardizasyonu)
```bash
# Test:
python -m unittest tests.test_smoke -v
# Beklenen: Tüm testler geçiyor (2803+ pass)
```

### 4. Dual STT Cleanup
```bash
# Gemini modunda test:
# config/api_keys.json'da backend_type="gemini" iken:
python main.py
# Beklenen: "[StreamingSTT]" log'u YOK (StreamingSTT çalışmıyor)
# Beklenen: Gemini Live API transkripsiyonu çalışıyor
```

---

## Faz 2 Doğrulama (VAD + Callback + Task + State Machine + Windows TTS)

### 1. Dual VAD Cleanup
```bash
python main.py
# Beklenen: "[VAD] Konusma basladi" log'u YOK (kaldırıldı)
# Beklenen: Ollama STT çalışıyor (FahrettinVAD ile)
```

### 2. Task Management
```bash
# STT'yi zorla çökert (geçici hata enjekte ederek):
# Beklenen: Max 3 restart, sonra "ERR: STT 3 kez çöktü" log'u
```

### 3. State Machine
```bash
python main.py
# Beklenen: UI state geçişleri tutarlı
# THINKING → MUTED geçersiz → state değişmez, log basılır
```

---

## Full Pipeline Smoke Test

```bash
# Ollama modu
sudo -E python main.py
# Sesli komut: "merhaba"
# Beklenen: 
#   1. VAD sesi algılar
#   2. STT transkripsiyon yapar
#   3. Ollama yanıt üretir
#   4. TTS yanıtı okur
#   5. Tüm UI state'leri doğru gösterir
```

---

## Test Komutları Özeti

| Test | Komut | Beklenen |
|------|-------|----------|
| Tüm unit testler | `python -m unittest discover tests -v` | 2803+ pass, 0 fail |
| Ollama smoke | `sudo -E python main.py` | Sesli asistan çalışır |
| Gemini smoke | `python main.py` | Sesli asistan çalışır |
| safe_call thread | Yeni test | Exception yok |
| State machine | Yeni test | Geçersiz geçişler engellenir |
| Provider contract | Yeni test | send_text/send_audio doğru |
