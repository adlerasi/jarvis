# UI Refactor — Strateji ve Kurallar

> **Durum: 🔴 HENÜZ UYGULANMADI** — Bu doküman hedef mimariyi tanimlar.  
> `ui.py` (1800+ satir) hala tek parça halindedir.  
> `health.py` de henuz ayrılmamıştır.  
> Asagidaki yapi planlanan hedef mimaridir.

> Bu doküman `REFACTOR_COMMAND_UI.md`'nin strateji/kural bölümüdür.
> Bkz. [UI_REFACTOR_PHASE1.md](UI_REFACTOR_PHASE1.md) — ui.py refactor
> Bkz. [UI_REFACTOR_PHASE2.md](UI_REFACTOR_PHASE2.md) — health.py refactor

---

## 🛡️ GERİYE UYUMLULUK STRATEJİSİ

### Aşama 1: Yeni Modülleri Oluştur, Eski Metodları Delegate Et

```python
# ui.py içinde (geçici)
from ui.panels.left_panel import LeftPanel

class JarvisUI:
    def __init__(self):
        # ...
        self._left_panel = LeftPanel()

    def _draw_left_panel(self, c):
        # Eski kodu sil, yeni modüle yönlendir
        self._left_panel.draw(c, x0, y0, width, height, self._panel_focus, self._panel_focus_until)
```

### Aşama 2: Tam Facade Yap

```python
# ui/__init__.py (yeni)
from .main_window import MainWindow
# ... tüm bileşenler

class JarvisUI:
    """Artık sadece bir koordinatör."""
```

### Aşama 3: Eski ui.py'yi Sil

- Eski `ui.py` → `ui/_legacy_ui.py` olarak yeniden adlandır
- 1 hafta sonra sil

---

## 🎯 COHESION HEDEFLERİ

| Modül | Mevcut Cohesion | Hedef Cohesion |
|-------|----------------|---------------|
| `ui.py` | 0.05 | **Silinecek** (Facade) |
| `ui/main_window.py` | — | **0.65+** |
| `ui/components/base_button.py` | — | **0.80+** |
| `ui/panels/cards/system_card.py` | — | **0.70+** |
| `ui/panels/agent_panel.py` | — | **0.60+** |
| `health.py` | 0.06 | **Silinecek** (Facade) |
| `health/file_finder.py` | — | **0.75+** |
| `health/formatters/heart_formatter.py` | — | **0.90+** |

---

## ⚠️ AJAN UYARILARI

1. **Hiçbir dosya 200 satırı geçmemeli.** Aşılırsa parçala.
2. **Bir dosyada "ve" kelimesiyle açıklanan sorumluluk varsa** ihlal vardır.
3. **Import döngüsü oluşturma.** `from . import module` kullan.
4. **Her refactor sonrası test et.** Uygulama açılmalı, butonlar çalışmalı.
5. **Eski dosyaları hemen silme.** Önce delegate et, sonra sil.

---

## 📏 DOSYA BOYUT KURALLARI

| Dosya Tipi | Maksimum Satır |
|-----------|---------------|
| `__init__.py` (facade) | **80 satır** |
| Bileşen sınıfı | **120 satır** |
| Yardımcı modül | **100 satır** |
| Test dosyası | **150 satır** |
| Koordinatör/Manager | **150 satır** |
| **KESİN KURAL** | **200 satır** (hiçbir dosya geçemez) |

> **İHLAL EDİLİRSE:** Ajan dosyayı tekrar parçalamak zorundadır.

---

## 📂 HEDEF DİZİN YAPISI

```
ui/
├── __init__.py              # Facade (max 80)
├── main_window.py           # Pencere yönetimi (max 120)
├── layout.py                # Layout yöneticisi (max 120)
├── sound_manager.py         # Ses efektleri (max 80)
├── orb_canvas.py            # Orb grafiği (max 120)
├── theme.py                 # Renk/tema sabitleri (max 50)
├── components/
│   ├── base_button.py       # HoverButton, BracketButton (max 120)
│   ├── input_bar.py         # Metin girişi (max 100)
│   ├── volume_slider.py     # Ses kaydırıcı (max 80)
│   └── voice_selector.py    # Ses seçici (max 80)
├── panels/
│   ├── left_panel.py        # Sol panel (max 120)
│   ├── right_panel.py       # Sağ panel (max 100)
│   ├── agent_panel.py       # ACA panel (max 120)
│   ├── settings_panel.py    # Ayarlar (max 120)
│   └── cards/
│       ├── base_card.py     # Temel kart (max 80)
│       ├── time_card.py     # Saat kartı (max 60)
│       ├── weather_card.py  # Hava durumu (max 60)
│       ├── system_card.py   # Sistem (max 100)
│       └── health_card.py   # Sağlık (max 50)
└── animation/
    ├── animator.py          # Animasyon motoru (max 120)
    └── background.py        # Arka plan (max 80)

health/
├── __init__.py              # Facade (max 80)
├── config.py                # Yapılandırma (max 50)
├── query_parser.py          # Sorgu ayrıştırma (max 100)
├── file_finder.py           # Dosya bulma (max 80)
├── loaders/
│   ├── base.py              # Soyut loader (max 40)
│   ├── hae_loader.py        # HealthAutoExport (max 80)
│   ├── simple_loader.py     # Basit JSON (max 50)
│   └── loader_factory.py    # Loader fabrikası (max 40)
├── metrics/
│   ├── registry.py          # Metrik kaydı (max 60)
│   └── extractor.py         # Metrik çıkarıcı (max 60)
├── formatters/
│   ├── base.py              # Soyut formatter (max 40)
│   ├── heart_formatter.py   # Kalp (max 40)
│   ├── activity_formatter.py # Aktivite (max 50)
│   ├── walking_formatter.py # Yürüyüş (max 40)
│   ├── sleep_formatter.py   # Uyku (max 30)
│   ├── oxygen_formatter.py  # Oksijen (max 30)
│   ├── audio_formatter.py   # Ses (max 30)
│   ├── daylight_formatter.py # Gün ışığı (max 30)
│   ├── default_formatter.py # Varsayılan (max 60)
│   ├── formatter_factory.py # Formatter fabrikası (max 50)
│   └── welcome_formatter.py # Karşılama (max 60)
└── analysis/
    └── workout_analyzer.py  # Antrenman analizi (max 120)
```
