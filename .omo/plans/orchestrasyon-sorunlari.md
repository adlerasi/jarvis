# Orkestrasyon Sorunları ve Çözüm Planı

## Tespit Edilen Sorunlar

---

### SORUN 1 (ÇÖZÜLDÜ) — SkillEngine çift modül yüklemesi (Double Import)

| Alan | Detay |
|---|---|
| **Dosya** | `core/_skill_engine.py:_load_skill_from_path()` |
| **Severity** | 🔴 Critical |
| **Etki** | ACA "henuz baslatilmadi" hatası. Tüm `route_*_request()` fonksiyonlarındaki modül-seviyesi globaller (`_agent_manager`, vs.) engine kopyasında `None` kalıyor. |
| **Kök neden** | `importlib.util.module_from_spec()` + `exec_module()` aynı `.py` dosyasını **ikinci bir Python modül nesnesi** olarak yükler. Normal import (`from skills.agent.agent_skill import X`) ile bu kopya ayrı namespace'e sahip olur. 18 skill'in tamamında aynı risk mevcut. |
| **Çözüm** | `_load_skill_from_path()` artık `sys.modules`'ta aynı `__file__` yoluna sahip mevcut modülü arar, bulursa **yeniden kullanır** (yeniden yüklemez). `force_reload=True` parametresi ile reload/watcher durumlarında zorla yeniden yükler. |
| **Kapsam** | Tüm 18 skill — hepsinde `__init__.py` + `*_skill.py` var, hepsi SkillEngine tarafından importlanabilir. |

---

### SORUN 2 — SkillEngine thread safety (Race condition)

| Alan | Detay |
|---|---|
| **Dosya** | `core/_skill_engine.py` satır 309-334 (route + _skills dict) |
| **Severity** | 🟡 Medium |
| **Etki** | Watcher thread'i `reload_skill()` ile `self._skills` dict'ini değiştirirken, `route()` aynı dict'i okursa `RuntimeError: dictionary changed size during iteration` veya yarı-güncel state oluşabilir. |
| **Kök neden** | `route()` `list(self._skills.items())` ile kopya alır (iterator safety), ancak `info.route_func` çağrısı sırasında `enable_skill()` aynı `info`'nun `route_func`'unu değiştirebilir. Hiçbir `threading.Lock` kullanılmıyor. |
| **Çözüm** | `_skills`, `_routers`, `_folder_map` erişimlerini `threading.Lock` ile korumak. `route()` içinde lock al, kopyala, release et. Reproducibility zor ama crash potansiyeli var. |

---

### SORUN 3 — Test tool_registry count (41 vs 40)

| Alan | Detay |
|---|---|
| **Dosya** | `tests/test_tool_registry.py` + `tests/test_smoke.py` (6 test) |
| **Severity** | 🟢 Low (pre-existing) |
| **Etki** | 6 test hep FAILED: `AssertionError: 41 != 40` |
| **Kök neden** | `agent_execute_goal` tool'u eklendiğinde `VALID_TOOLS` 41'e çıktı ama test beklentisi güncellenmedi. Handler'ların hepsi mevcut (41/41). |
| **Çözüm** | Testlerde `40` → `41` olarak güncellemek. |

---

### SORUN 4 — `_user_initiated` hiç sıfırlanmıyor

| Alan | Detay |
|---|---|
| **Dosya** | `main.py` satır 370/401/482 vs `core/agent/agent_manager.py` satır 233-239 |
| **Severity** | 🟢 Low |
| **Etki** | İlk kullanıcı etkileşiminden sonra `_user_initiated` hep `True` kalır. `execute_goal()`'daki güvenlik kontrolü etkisiz hale gelir — LLM'in kendi kendine ACA başlatmasını engelleyemez. |
| **Kök neden** | Bayrak set ediliyor ama hiç `False` yapılmıyor (init hariç). |
| **Çözüm** | Goal tamamlanınca veya timeout olunca `_user_initiated = False` yapılabilir. Veya her `_on_stt_text`/`_on_text_command` öncesi True, sonrası False. |

---

### SORUN 5 — `execute_goal` dönüş tipi string (goal_id) ama UI/agent_skill string bekliyor

| Alan | Detay |
|---|---|
| **Dosya** | `core/agent/agent_manager.py:228` → `skills/agent/agent_skill.py:81` |
| **Severity** | 🟢 Low (çalışıyor) |
| **Etki** | `execute_goal()` goal_id döndürür (`"ACA: Hedef baslatildi (ID: goal_...)"`). `route_agent_request` bu string'i direkt döndürür, UI da TTS ile okur. Kullanıcı goal_id duyar. |
| **Kök neden** | Tasarım gereği string dönüş, ama goal_id'nin TTS'de okunması kullanıcı deneyimi için gereksiz. |
| **Çözüm** | `route_agent_request` dönüşünü sadeleştirmek: `"Hedef baslatildi."` gibi. |

---

### SORUN 6 — AgentManager `_emit_update` thread safety

| Alan | Detay |
|---|---|
| **Dosya** | `core/agent/agent_manager.py` `_emit_update()` |
| **Severity** | 🟢 Low |
| **Etki** | `_emit_update()` worker thread'den çağrılır, `on_state_update` callback'i UI'a state gönderir. UI `safe_call` ile main thread'e atlar (doğru), ama `get_goal_status()` lock alır mı? |
| **Kök neden** | `get_goal_status()` `self._lock` alır (line 298: `with self._lock:`). Bu doğru. Ancak `_emit_update` lock almaz ama `get_goal_status` alır — yeterli. |
| **Çözüm** | Gerek yok — zaten doğru çalışıyor. Sadece not. |

---

## Çözüm Sırası (Önerilen)

| # | Sorun | Effort | Risk | Yapılacak |
|---|---|---|---|---|
| 1 | ~~Double import~~ | ✅ | — | Çözüldü |
| 2 | Thread safety | 2-3 dosya | Orta | `threading.Lock` ekle |
| 3 | Test count fix | 1 test dosyası | Düşük | 40→41 |
| 4 | `_user_initiated` reset | 2-3 satır | Düşük | Goal sonu/False |
| 5 | Goal ID TTS | 1 satır | Düşük | Mesajı sadeleştir |
