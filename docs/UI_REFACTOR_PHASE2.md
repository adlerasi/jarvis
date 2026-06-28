# UI Refactor — Faz 2: health.py → Modüllere Bölünmesi

> **Durum: 🔴 HENÜZ UYGULANMADI** — `health.py` henüz modüllere ayrilmamistir.  
> Bu doküman hedef mimariyi tanimlar.

> Bu doküman `REFACTOR_COMMAND_UI.md`'nin Faz 2 bölümüdür.
> Bkz. [UI_REFACTOR_GUIDE.md](UI_REFACTOR_GUIDE.md) — kurallar ve strateji
> Bkz. [UI_REFACTOR_PHASE1.md](UI_REFACTOR_PHASE1.md) — ui.py refactor

---

## 🔴 FAZ 2: health.py → 10 Modüle Bölünmesi

### 2.1 `health/__init__.py` (Facade, max 80 satır)

```python
"""Health module — Public API."""
from __future__ import annotations
from .query_parser import QueryParser
from .file_finder import FileFinder
from .loaders.loader_factory import LoaderFactory
from .metrics.extractor import MetricsExtractor
from .formatters.formatter_factory import FormatterFactory
from .analysis.workout_analyzer import WorkoutAnalyzer
from .config import STALE_WARN_MINUTES

__all__ = ["get_health_data", "get_welcome_health_summary"]

def get_health_data(query: str = "all") -> str:
    parser = QueryParser()
    target_date = parser.extract_target_date(query)

    finder = FileFinder()
    source_file = finder.resolve(target_date)
    if not source_file:
        return _not_found_message()

    loader = LoaderFactory.get_loader(source_file)
    raw_data, timestamp, source_date = loader.load(source_file, target_date)

    extractor = MetricsExtractor()
    metrics = extractor.extract(raw_data, source_date)

    category = parser.categorize(query)
    if category == "analysis":
        analyzer = WorkoutAnalyzer()
        return analyzer.analyze(raw_data, metrics, query, source_date, timestamp)

    formatter = FormatterFactory.get_formatter(category)
    return formatter.format(metrics, timestamp)

def get_welcome_health_summary() -> str:
    finder = FileFinder()
    source_file = finder.resolve()
    if not source_file:
        return "Sağlık verilerin şu anda alınamadı."

    loader = LoaderFactory.get_loader(source_file)
    raw_data, timestamp, _ = loader.load(source_file)

    extractor = MetricsExtractor()
    metrics = extractor.extract(raw_data)

    from .formatters.welcome_formatter import WelcomeFormatter
    return WelcomeFormatter().format(metrics, timestamp)

def _not_found_message() -> str:
    import sys
    if sys.platform == "darwin":
        return ("Sağlık verisi bulunamadı. iPhone'da desteklenen bir sağlık dışa aktarma "
                "aracı kurup iCloud Drive > Auto Export > JARVIS klasörüne export ayarlaman gerekiyor.")
    return "Sağlık verisi bulunamadı. HealthAutoExport-YYYY-AA-GG.json dosyasını memory/health/ klasörüne kopyala."
```

### 2.2 `health/config.py` (max 50 satır)

```python
"""Health modülü yapılandırması."""
from __future__ import annotations
import os, sys
from pathlib import Path

IS_MACOS = os.name == "posix" and sys.platform == "darwin"
STALE_WARN_MINUTES = 120

if IS_MACOS:
    MOBILE_DOCS = Path.home() / "Library" / "Mobile Documents"
    HEALTH_DIR: Path = MOBILE_DOCS / "iCloud~com~ifunography~HealthExport" / "Documents" / "JARVIS"
    LEGACY_DIRS: list[Path] = [
        MOBILE_DOCS / "com~apple~CloudDocs" / "Auto Export" / "JARVIS",
        MOBILE_DOCS / "com~apple~CloudDocs" / "JARVIS",
    ]
    LEGACY_FILE: Path | None = MOBILE_DOCS / "com~apple~CloudDocs" / "JARVIS" / "health_data.json"
else:
    HEALTH_DIR = BASE_DIR / "memory" / "health"
    LEGACY_DIRS = []
    LEGACY_FILE = None

BASE_DIR = Path(__file__).resolve().parent.parent
```

### 2.3 `health/query_parser.py` (max 100 satır)

```python
"""Sorgu ayrıştırıcı — kullanıcı sorgusundan tarih/kategori çıkarır."""
from __future__ import annotations
import re
from datetime import datetime, timedelta

# Tarih pattern'leri
_RELATIVE_DAYS = {
    "bugün": 0, "dün": -1, "önceki gün": -2, "üç gün önce": -3,
    "haftaya": 7, "geçen hafta": -7,
}
_MONTH_NAMES = ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran",
                "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]

# Kategori pattern'leri
_CATEGORY_KEYWORDS = {
    "heart": ["nabız", "kalp", "heart", "hrv", "pulse"],
    "activity": ["aktivite", "adım", "step", "yürüyüş", "kalori", "karbonhidrat",
                  "protein", "yağ", "besin", "enerji", "mesafe"],
    "sleep": ["uyku", "sleep", "uyanma"],
    "oxygen": ["oksijen", "spo2", "oxygen"],
    "daylight": ["gün ışığı", "güneş", "daylight", "süre"],
    "audio": ["ses", "gürültü", "audio", "noise", "decibel"],
    "analysis": ["analiz", "genel", "özet", "all", "analysis"],
}

class QueryParser:
    def extract_target_date(self, query: str) -> str | None:
        """Sorgudan hedef tarihi çıkar."""
        q = query.lower().strip()

        # Bugün, dün, vb.
        for word, offset in _RELATIVE_DAYS.items():
            if word in q:
                d = datetime.now() + timedelta(days=offset)
                return d.strftime("%Y-%m-%d")

        # Ay/gün pattern: "15 ocak", "ocak 15"
        m = re.search(r"(\d{1,2})\s+(ocak|şubat|mart|...)", q)
        if m: return f"2024-{_month_num(m.group(2)):02d}-{int(m.group(1)):02d}"

        m = re.search(r"(ocak|şubat|mart|...)\s+(\d{1,2})", q)
        if m: return f"2024-{_month_num(m.group(1)):02d}-{int(m.group(2)):02d}"

        return None  # En son dosyayı kullan

    def categorize(self, query: str) -> str:
        """Sorguyu kategoriye ayır."""
        q = query.lower()
        for cat, keywords in _CATEGORY_KEYWORDS.items():
            if any(kw in q for kw in keywords):
                return cat
        return "all"

    @staticmethod
    def _month_num(name: str) -> int:
        try: return _MONTH_NAMES.index(name) + 1
        except ValueError: return 1
```

### 2.4 `health/file_finder.py` (max 80 satır)

```python
"""Dosya bulucu — sağlık verisi JSON dosyasını bulur."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from .config import HEALTH_DIR, LEGACY_DIRS, LEGACY_FILE

class FileFinder:
    def resolve(self, target_date: str | None = None) -> Path | None:
        """En güncel sağlık verisi dosyasını bul."""
        if not HEALTH_DIR.exists():
            # Legacy dizinlerde ara
            if LEGACY_FILE and LEGACY_FILE.exists():
                return LEGACY_FILE
            for d in LEGACY_DIRS:
                if d.exists():
                    files = sorted(d.glob("HealthAutoExport-*.json"))
                    if files: return files[-1]
            return None

        files = sorted(HEALTH_DIR.glob("HealthAutoExport-*.json"))
        if not files:
            for d in LEGACY_DIRS:
                if d.exists():
                    files = sorted(d.glob("HealthAutoExport-*.json"))
                    if files: return files[-1]
            return None

        if target_date:
            # Tarihe göre filtrele
            matching = [f for f in files if target_date in f.name]
            if matching: return matching[-1]

        return files[-1]  # En son dosya
```

### 2.5 `health/loaders/base.py` (max 40 satır)

```python
"""Base loader — soyut veri yükleme arayüzü."""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path

class BaseLoader(ABC):
    @abstractmethod
    def load(self, file_path: Path, target_date: str | None = None):
        """Dosyadan sağlık verisini yükle.
        Returns: (raw_data, timestamp, source_date)
        """
```

### 2.6 `health/loaders/hae_loader.py` (max 80 satır)

```python
"""HealthAutoExport JSON yükleyici."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from .base import BaseLoader

class HealthAutoExportLoader(BaseLoader):
    def load(self, file_path: Path, target_date: str | None = None):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Metadata
        timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
        source_date = target_date or file_path.stem.split("HealthAutoExport-")[-1]

        return data, timestamp, source_date
```

### 2.7 `health/loaders/simple_loader.py` (max 50 satır)

```python
"""Basit JSON yükleyici — legacy destek."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from .base import BaseLoader

class SimpleLoader(BaseLoader):
    def load(self, file_path: Path, target_date: str | None = None):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
        return data, timestamp, "latest"
```

### 2.8 `health/loaders/loader_factory.py` (max 40 satır)

```python
"""Loader fabrikası — dosya adına göre uygun loader'ı seçer."""
from __future__ import annotations
from pathlib import Path
from .hae_loader import HealthAutoExportLoader
from .simple_loader import SimpleLoader

class LoaderFactory:
    @staticmethod
    def get_loader(file_path: Path):
        if "HealthAutoExport" in file_path.name:
            return HealthAutoExportLoader()
        return SimpleLoader()
```

### 2.9 `health/metrics/registry.py` (max 60 satır)

```python
"""Metrik kaydı — hangi metriklerin hangi formatter'a gideceğini tanımlar."""
from __future__ import annotations

METRIC_REGISTRY = {
    "heart": {
        "fields": ["heart_rate", "hrv", "resting_heart_rate"],
        "display_name": "Kalp",
        "unit": "bpm",
    },
    "activity": {
        "fields": ["steps", "calories", "distance", "carbohydrates",
                    "protein", "fat", "energy"],
        "display_name": "Aktivite",
        "unit": "adım",
    },
    "sleep": {
        "fields": ["sleep_hours", "deep_sleep", "rem_sleep", "wake_count"],
        "display_name": "Uyku",
        "unit": "saat",
    },
    "oxygen": {
        "fields": ["spo2_avg", "spo2_min"],
        "display_name": "Oksijen",
        "unit": "%",
    },
    "daylight": {
        "fields": ["daylight_minutes"],
        "display_name": "Gün Işığı",
        "unit": "dk",
    },
    "audio": {
        "fields": ["audio_level_avg", "audio_level_max"],
        "display_name": "Ses",
        "unit": "dB",
    },
}
```

### 2.10 `health/metrics/extractor.py` (max 60 satır)

```python
"""Metrik çıkarıcı — ham veriden metrik değerlerini çıkarır."""
from __future__ import annotations
from .registry import METRIC_REGISTRY

class MetricsExtractor:
    def extract(self, raw_data: dict, source_date: str | None = None) -> dict:
        """Ham JSON'dan anlamlı metrikler çıkar."""
        metrics = {}

        for category, config in METRIC_REGISTRY.items():
            category_data = {}
            for field in config["fields"]:
                value = self._find_field(raw_data, field)
                if value is not None:
                    category_data[field] = value
            if category_data:
                metrics[category] = category_data

        return metrics

    def _find_field(self, data: dict, field: str) -> float | None:
        """JSON içinde recursive field arama."""
        if field in data:
            return data[field]

        for key, value in data.items():
            if isinstance(value, dict):
                result = self._find_field(value, field)
                if result is not None:
                    return result

        return None
```

### 2.11 `health/formatters/base.py` (max 40 satır)

```python
"""Base formatter — soyut metrik formatlama arayüzü."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

class BaseFormatter(ABC):
    @abstractmethod
    def format(self, metrics: dict, timestamp: datetime) -> str:
        """Metrikleri insan okunabilir metne dönüştür."""
```

### 2.12 `health/formatters/heart_formatter.py` (max 40 satır)

```python
"""Kalp metrik formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class HeartFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("heart", {})
        parts = ["[KALP]"]
        if "heart_rate" in data:
            parts.append(f"Nabız: {data['heart_rate']} bpm")
        if "hrv" in data:
            parts.append(f"HRV: {data['hrv']} ms")
        if "resting_heart_rate" in data:
            parts.append(f"Dinlenme: {data['resting_heart_rate']} bpm")
        return "\n".join(parts) if len(parts) > 1 else "Kalp verisi bulunamadı."
```

### 2.13 `health/formatters/activity_formatter.py` (max 50 satır)

```python
"""Aktivite metrik formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class ActivityFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("activity", {})
        parts = ["[AKTIVITE]"]
        if "steps" in data:
            parts.append(f"Adım: {data['steps']:,}")
        if "calories" in data:
            parts.append(f"Kalori: {data['calories']:.0f} kcal")
        if "distance" in data:
            parts.append(f"Mesafe: {data['distance']:.1f} km")
        return "\n".join(parts) if len(parts) > 1 else "Aktivite verisi bulunamadı."
```

### 2.14 `health/formatters/walking_formatter.py` (max 40 satır)

```python
"""Yürüyüş detay formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class WalkingFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("walking", metrics.get("activity", {}))
        parts = ["[YURUYUS]"]
        if "steps" in data:
            parts.append(f"Toplam adım: {data['steps']:,}")
        if "walking_speed" in data:
            parts.append(f"Hız: {data['walking_speed']:.1f} km/s")
        return "\n".join(parts)
```

### 2.15 `health/formatters/sleep_formatter.py` (max 30 satır)

```python
"""Uyku metrik formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class SleepFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("sleep", {})
        parts = ["[UYKU]"]
        if "sleep_hours" in data:
            parts.append(f"Süre: {data['sleep_hours']:.1f} saat")
        if "deep_sleep" in data:
            parts.append(f"Derin uyku: {data['deep_sleep']:.1f} saat")
        return "\n".join(parts)
```

### 2.16 `health/formatters/oxygen_formatter.py` (max 30 satır)

```python
"""Oksijen metrik formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class OxygenFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("oxygen", {})
        parts = ["[OKSIJEN]"]
        if "spo2_avg" in data:
            parts.append(f"SpO₂: {data['spo2_avg']:.1f}%")
        return "\n".join(parts)
```

### 2.17 `health/formatters/audio_formatter.py` (max 30 satır)

```python
"""Ses metrik formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class AudioFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("audio", {})
        parts = ["[SES]"]
        if "audio_level_avg" in data:
            parts.append(f"Ortalama: {data['audio_level_avg']:.0f} dB")
        return "\n".join(parts)
```

### 2.18 `health/formatters/daylight_formatter.py` (max 30 satır)

```python
"""Gün ışığı metrik formatter'ı."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class DaylightFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        data = metrics.get("daylight", {})
        parts = ["[GUN ISIGI]"]
        if "daylight_minutes" in data:
            parts.append(f"Süre: {data['daylight_minutes']:.0f} dk")
        return "\n".join(parts)
```

### 2.19 `health/formatters/default_formatter.py` (max 60 satır)

```python
"""Varsayılan formatter — tüm metrikleri göster."""
from __future__ import annotations
from datetime import datetime
from .heart_formatter import HeartFormatter
from .activity_formatter import ActivityFormatter
from .sleep_formatter import SleepFormatter
from .oxygen_formatter import OxygenFormatter

class DefaultFormatter:
    def format(self, metrics: dict, timestamp: datetime) -> str:
        parts = [f"📊 Sağlık Özeti ({timestamp.strftime('%d.%m.%Y %H:%M')})"]
        parts.append("=" * 30)

        formatters = [
            HeartFormatter(), ActivityFormatter(),
            SleepFormatter(), OxygenFormatter(),
        ]
        for f in formatters:
            result = f.format(metrics, timestamp)
            if result and "bulunamadı" not in result:
                parts.append("")
                parts.append(result)

        return "\n".join(parts)
```

### 2.20 `health/formatters/formatter_factory.py` (max 50 satır)

```python
"""Formatter fabrikası — kategoriye göre uygun formatter'ı seçer."""
from __future__ import annotations
from .heart_formatter import HeartFormatter
from .activity_formatter import ActivityFormatter
from .sleep_formatter import SleepFormatter
from .oxygen_formatter import OxygenFormatter
from .daylight_formatter import DaylightFormatter
from .audio_formatter import AudioFormatter
from .default_formatter import DefaultFormatter

_FORMATTER_MAP = {
    "heart": HeartFormatter,
    "activity": ActivityFormatter,
    "sleep": SleepFormatter,
    "oxygen": OxygenFormatter,
    "daylight": DaylightFormatter,
    "audio": AudioFormatter,
}

class FormatterFactory:
    @staticmethod
    def get_formatter(category: str):
        formatter_cls = _FORMATTER_MAP.get(category, DefaultFormatter)
        return formatter_cls()
```

### 2.21 `health/formatters/welcome_formatter.py` (max 60 satır)

```python
"""Karşılama mesajı formatter'ı — kısa günlük özet."""
from __future__ import annotations
from datetime import datetime
from .base import BaseFormatter

class WelcomeFormatter(BaseFormatter):
    def format(self, metrics: dict, timestamp: datetime) -> str:
        parts = []

        activity = metrics.get("activity", {})
        if "steps" in activity:
            parts.append(f"🚶 {activity['steps']:,} adım")

        heart = metrics.get("heart", {})
        if "heart_rate" in heart:
            parts.append(f"❤️ {heart['heart_rate']} bpm")

        sleep = metrics.get("sleep", {})
        if "sleep_hours" in sleep:
            parts.append(f"😴 {sleep['sleep_hours']:.1f}s")

        return " · ".join(parts) if parts else "Bugün henüz sağlık verisi yok."
```

### 2.22 `health/analysis/workout_analyzer.py` (max 120 satır)

```python
"""Antrenman analizörü — derinlemesine egzersiz analizi."""
from __future__ import annotations
from datetime import datetime

class WorkoutAnalyzer:
    def analyze(self, raw_data: dict, metrics: dict, query: str,
                source_date: str, timestamp: datetime) -> str:
        """Kullanıcı sorgusuna göre antrenman analizi yap."""
        parts = ["[ANTRENMAN ANALIZI]"]

        # Kalp verisi
        heart = metrics.get("heart", {})
        if "heart_rate" in heart:
            hr = heart["heart_rate"]
            zone = self._heart_rate_zone(hr)
            parts.append(f"Kalp: {hr} bpm ({zone})")

        # Aktivite
        activity = metrics.get("activity", {})
        if "steps" in activity:
            parts.append(f"Adım: {activity['steps']:,}")

        # Süre
        if "workout_minutes" in raw_data:
            parts.append(f"Süre: {raw_data['workout_minutes']} dk")

        return "\n".join(parts)

    def _heart_rate_zone(self, hr: float) -> str:
        if hr < 60: return "Dinlenme"
        if hr < 100: return "Hafif"
        if hr < 140: return "Orta"
        return "Yüksek"
```
