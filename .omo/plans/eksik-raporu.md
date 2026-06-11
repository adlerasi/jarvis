# Eksik Tarama Raporu & Onarım Planı

**Tarih**: 2026-06-11
**Kapsam**: specs/001-autonomous-computer-agent, 002-aca-subsystem, 003-tam-assimilasyon

---

## Özet

| Spec | FR Sayısı | Tamam | Eksik |
|------|-----------|-------|-------|
| 001 | 13 | 13 | 0 |
| 002 | 37 | 37 | 0 |
| 003 | 26 | 24 | 2 |

---

## Eksik #1 — Agent Panel Log Bölümü (FR-012)

**Spec**: Log entries from AgentManager._log() MUST appear in the panel's scrollable log section automatically.

**Mevcut Durum**: 
- `ui.py`'de `self.agent_log: list[str] = []` tanımlı ama **hiç kullanılmıyor**
- `_update_agent_state()` `agent_log` field'ını güncellemiyor
- `get_goal_status()` state dict'inde `logs` alanı yok
- Agent panelde scrollable log bölümü yok

**Yapılacaklar**:
1. `agent_manager.py` → `get_goal_status()`'a `logs` alanı ekle
2. `agent_manager.py` → `_log()` metodunda log geçmişini tut
3. `ui.py` → `_update_agent_state()`'de `agent_log`'u güncelle
4. `ui.py` → `_draw_agent_panel()`'e scrollable log bölümü ekle

---

## Eksik #2 — Task Notification (US4/SC örtük)

**Spec**: Desktop notification on task start/complete (User Story 4, Success Criteria'da örtük)

**Mevcut Durum**:
- `AgentManager._run_goal_loop()` task başında/bitişinde `notify()` çağırmıyor
- `AgentManager._finalize_goal()` sadece `self._log()` yapıyor
- main.py'de notification sadece startup/error/shutdown için kullanılıyor

**Yapılacaklar**:
1. `agent_manager.py` → `_run_goal_loop()`'da task başlangıcında `notify()` çağır
2. `agent_manager.py` → `_finalize_goal()`'da task bitişinde `notify()` çağır

---

## Geliştirme #3 — Agent Panel Progress Bar

**Spec**: User Story 3'te "progress bar advances" geçiyor

**Mevcut Durum**: Step list var ama görsel progress bar yok

**Yapılacaklar**:
1. `ui.py` → `_draw_agent_panel()`'e adım sayısına göre progress bar ekle

---

## Geliştirme #4 — Approval Mode UI Toggle

**Mevcut Durum**: `agent_approval_mode` state'de var ama UI'da kontrol yok

**Yapılacaklar**:
1. `ui.py` → Agent panele approval mode toggle düğmesi ekle
2. `main.py` → toggle callback'ini bağla

---

## Geliştirme #5 — Runtime Config UI

**Mevcut Durum**: `max_steps`/`max_duration` sadece `__init__` parametresi

**Yapılacaklar**:
1. `agent_manager.py` → runtime config setter'ları ekle
2. `ui.py` → Agent panele ayar kontrolleri ekle

---

## Önerilen Onarım Sırası

```
1. Eksik #1 — Agent Panel Log Bölümü (FR-012)
2. Eksik #2 — Task Notification
3. Geliştirme #3 — Progress Bar
4. Geliştirme #4 — Approval Mode Toggle
5. Geliştirme #5 — Runtime Config
```
