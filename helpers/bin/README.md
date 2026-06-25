# helpers/bin — Yardımcı Binary'ler

Bu dizin, JARVIS'in ihtiyaç duyduğu yardımcı çalıştırılabilir dosyalar içindir.
Şu an boş — gerekli binary'ler sistem PATH'te mevcut olduğu sürece sorun yok.

> **Not:** Bu dizin Linux/macOS'ta genelde boştur çünkü bağımlılıklar (ffmpeg, mpg123)
> sistem paket yöneticisi ile kurulur. Windows'ta nircmd.exe gibi Windows'a özel
> binary'ler buraya konur.

## Gerekebilecek Binary'ler

| Binary | Ne işe yarar | Nereden indirilir |
|--------|-------------|-------------------|
| `nircmd.exe` | Windows ses ayarları | https://www.nirsoft.net/utils/nircmd.html |
| `ffmpeg` / `ffprobe` | Ses dosyası dönüşüm / kesme | `apt install ffmpeg` veya https://ffmpeg.org |
| `mpg123` | MP3 oynatıcı (TTS yedek) | `apt install mpg123` veya https://www.mpg123.de |

## Kurulum

Binary'leri bu dizine koyun veya sistem PATH'inizde olduğundan emin olun.
Windows'ta `.exe` uzantılı olmalıdır.

```powershell
# Örnek: nircmd.exe bu dizine kopyalayın
```
```bash
# Linux/macOS: sistem paket yöneticisi ile kurun
sudo apt install ffmpeg mpg123   # Debian/Ubuntu
```
