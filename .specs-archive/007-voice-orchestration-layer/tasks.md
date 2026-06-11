# Tasks: Voice Orchestration Layer

**Input**: spec.md (007-voice-orchestration-layer)

**Tests**: TEST-FIRST yaklaşımı — realtime testler, mock yok

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Mevcut kodda eksik düzeltmeler

- [x] T001 main.py:656 — `set_state("ERROR")` düzeltmesi
- [x] T002 gemini_provider.py:322 — `Queue(maxsize=200)` düzeltmesi

---

## Phase 2: Realtime Testler (Priority: P1)

**Purpose**: Her FR için realtime test — mock/placeholder yasak, gerçek nesnelerle çalışan test

- [x] T003 [P] [US1] State machine geçiş testi — `tests/test_state_machine.py`
- [x] T004 [P] [US2] State geçiş UI senkronizasyon testi — `tests/test_state_ui.py`
- [x] T005 [US3] Barge-in entegrasyon testi — `tests/test_barge_in.py` + timing <500ms

---

## Phase 3: Doğrulama & Polish

- [x] T006 Tüm `ui.set_state` çağrılarının `set_state` üzerinden geçtiğini doğrula
- [x] T007 Queue limit testi + overflow fix (`gemini_provider.py`)
- [x] T008 Final diagnostics — tüm değişiklik dosyalarında 0 hata

---

## Dependencies & Execution Order

- **Phase 1**: ✅ Zaten tamam (kod düzeltmeleri yapıldı)
- **Phase 2 (T003-T005)**: Bağımsız, paralel
- **Phase 3 (T006-T008)**: Phase 2 sonrası

### Parallel Opportunities

- T003, T004, T005 tamamen bağımsız — paralel yazılabilir
- T006 bağımsız grep scan
- T007 T005'e dayanır

## Implementation Strategy

1. Phase 1 zaten tamam — atla
2. Phase 2: Realtime testleri yaz ve çalıştır
3. Phase 3: Doğrula ve bitir
