# JARVIS UI & Health Refactor

> **Durum: 🔴 HENÜZ UYGULANMADI** — `ui.py` (1800+ satir) ve `health.py` henüz modüllere ayrilmamistir.  
> Alt dokümanlar hedef mimariyi tanimlar. Uygulama sirasinda buraya bakin.

> Bu dosya, ui.py ve health.py modüllerini cohesion prensiplerine göre parçalama ana indeksidir.
> **Toplam 1487 satır → 3 alt dokümana bölündü.**

---

## Alt Dokümanlar

| # | Doküman | Açıklama | Orijinal Satır |
|---|---------|----------|---------------|
| 1 | [UI_REFACTOR_PHASE1.md](UI_REFACTOR_PHASE1.md) | **FAZ 1:** ui.py → 18 modüle bölünmesi (kurallar + tüm kod şablonları) | ~735 |
| 2 | [UI_REFACTOR_PHASE2.md](UI_REFACTOR_PHASE2.md) | **FAZ 2:** health.py → 22 modüle bölünmesi (tüm kod şablonları) | ~695 |
| 3 | [UI_REFACTOR_GUIDE.md](UI_REFACTOR_GUIDE.md) | Strateji, cohesion hedefleri, ajan uyarıları, hedef dizin yapısı | ~55 |

---

## Hızlı Başvuru

**Kural:** Hiçbir dosya 200 satırı geçemez.
**Strateji:** Önce delegate et, sonra sil.
**Hedef:** ui.py (cohesion 0.05) ve health.py (0.06) → tamamen facade'a dönüşsün.

[Faz 1: ui.py → 18 Modül](UI_REFACTOR_PHASE1.md) ·
[Faz 2: health.py → 22 Modül](UI_REFACTOR_PHASE2.md) ·
[Strateji ve Kurallar](UI_REFACTOR_GUIDE.md)
