# Ajan Sistemi

## Ajan Mimarisi Genel Bakış

JARVIS'te **2 ajan sistemi** bulunur:

1. **ACA (Autonomous Computer Agent):** Otonom, çok adımlı görevler için. Observer → Planner → Executor → Reflection döngüsü ile çalışır. Karmaşık görevleri alt adımlara böler, her adım için tool/skill çağrısı yapar.
2. **Skill Managers:** Basit, doğrudan komutlar için. Regex pattern eşleşmesi ile AI'a gitmeden anında yanıt üretir.

### Pattern Karşılaştırması

| Özellik | ACA Agent | Skill Manager |
|---------|-----------|---------------|
| Pattern | Observer-Planner-Executor-Reflection | Reaktif routing |
| Karmaşıklık | Çok adımlı, otonom | Tek adımlı, deterministik |
| LLM Kullanımı | Evet (planlama + analiz) | Hayır |
| Tetikleyici | AgentManager çağrısı | Kullanıcı metni regex eşleşmesi |
| State | Goal → TaskGraph → TaskNode | Yok (stateless) |
| Onay | RiskLevel (NONE→HIGH) | Pattern doğrulaması |

## Ajan Listesi

### Ajan: ACA (Autonomous Computer Agent)

- **Rol:** Otonom görev yürütücü
- **Sorumluluk Alanı:** Çok adımlı, plan gerektiren karmaşık görevler
- **Tetikleyici Intent'ler:** `execute_goal()`, `run_task()`, otonom karar gerektiren işlemler
- **Kullandığı LLM:** Provider üzerinden (Gemini/Ollama)
- **Sistem Prompt'u:** planlayıcı + yürütücü prompt'ları `core/agent/prompts/` altında
- **Sahip Olduğu Skill'ler:** Tüm kayıtlı tool'lar (tool_registry.py), tüm skill'ler (skill_manager)
- **Bellek / Context Yönetimi:** `AgentMemory` (JSON + diction based)
- **Input Formatı:** `AgentGoal(goal_id, text)` — doğal dil hedef
- **Output Formatı:** `GoalStatus.COMPLETED/FAILED` + result string
- **Kod Lokasyonu:** `core/agent/agent_manager.py`

### Ajan: Skill Manager (Routing Engine)

- **Rol:** Anlık komut yönlendirici
- **Sorumluluk Alanı:** Basit, öngörülebilir komutlar (tarayıcı aç, saat kaç, hava durumu)
- **Tetikleyici Intent'ler:** `_on_text_command()` içinde LLM'den önce çağrılır
- **Kullandığı LLM:** Yok
- **Sistem Prompt'u:** Yok
- **Sahip Olduğu Skill'ler:** 18 skill (skills/ klasörü)
- **Bellek / Context Yönetimi:** Yok (stateless)
- **Input Formatı:** `route(user_text: str) → str | None`
- **Output Formatı:** Skill sonucu string veya None
- **Kod Lokasyonu:** `core/skill_manager.py` + `core/_skill_engine.py`

## ACA Agent Subsystem Detayı

AgentManager 5 alt bileşenden oluşur:

```
AgentManager
├── Observer (core/agent/observer.py)
│   ├── Sistem durumunu izler
│   └── Değişiklikleri algılar → event tetikler
│
├── Planner (core/agent/planner.py)
│   ├── Goal'i analiz eder
│   ├── TaskGraph oluşturur (alt adımlar)
│   └── Bağımlılıkları belirler
│
├── Executor (core/agent/executor.py)
│   ├── TaskGraph'deki node'ları sırayla çalıştırır
│   ├── Her node için tool/skill çağrısı yapar
│   └── Sonuçları toplar
│
├── Reflection (core/agent/reflection.py)
│   ├── Executor sonuçlarını değerlendirir
│   ├── Hata varsa yeniden planlama önerir
│   └── Tamamlanma kriterlerini doğrular
│
└── ApprovalManager (core/agent/approval_manager.py)
    ├── RiskLevel: NONE / LOW / MEDIUM / HIGH
    ├── Her aksiyon için risk değerlendirmesi
    └── MEDIUM+ için kullanıcı onayı
```

### ACA Yaşam Döngüsü

```
AgentManager.execute_goal(goal_text)
    │
    ├── 1. Observer.update_state()
    │       └── Mevcut sistem durumunu al
    │
    ├── 2. Planner.create_plan(goal, state)
    │       └── TaskGraph döndür
    │
    ├── 3. Executor.execute_graph(graph, callbacks)
    │       ├── Her node için:
    │       ├── ApprovalManager.approve(action)
    │       │       ├── RED → node cancelled
    │       │       └── APPROVED → execute
    │       ├── Tool/Skill çağrısı
    │       └── Sonucu kaydet
    │
    ├── 4. Reflection.evaluate(graph)
    │       ├── Başarılı → COMPLETED
    │       └── Başarısız → FAILED / yeniden planla
    │
    └── 5. Goal güncelle + callback
```

## Ajanlar Arası İletişim

```
main.py (JarvisLive)
    │
    ├── _on_text_command(text)
    │       ├── SkillManager.route(text)
    │       │       └── skill fonksiyonu → str
    │       └── Provider.send_text(text)
    │               └── LLM → tool call / yanıt
    │
    └── AgentManager (ACA)
            └── execute_goal(text)
                    ├── Observer: durum al
                    ├── Planner: task graph oluştur
                    ├── Executor: tool/skill çağır
                    └── Reflection: değerlendir
```

### İletişim Protokolü

| Gönderen | Alıcı | Yöntem | Veri |
|----------|-------|--------|------|
| Kullanıcı metni | SkillManager | `route(text)` | String → String/None |
| Kullanıcı metni | LLM Provider | `send_text(text)` | String → Stream |
| LLM Tool Call | _execute_tool | `TOOL_HANDLER_MAP` | tool_name, args → String |
| ACA Goal | AgentManager | `execute_goal(text)` | Goal → Status + Result |
| AgentManager | ApprovalManager | `approve(action)` | Action → bool |
| ACA node | Executor | `_run_node(node)` | TaskNode → Result |

## Ajan Yaşam Döngüsü (Skill Engine)

```
Skill Engine (core/_skill_engine.py)
    │
    ├── LOAD: skills/<name>/ dizinini tara
    │       ├── route_<name>_request() fonksiyonunu bul
    │       ├── SKILL.md metadata'sını parse et (opsiyonel)
    │       └── triggers.json pattern'lerini yükle (opsiyonel)
    │
    ├── WATCH: Hot-reload thread (3sn interval)
    │       ├── Yeni dosya → import + register
    │       ├── Değişen dosya → reload
    │       └── Silinen dosya → unregister
    │
    ├── ROUTE: route(text) çağrıldığında
    │       ├── Tüm aktif skill'leri sırayla dene
    │       └── İlk eşleşen sonucu döndür
    │
    └── UNLOAD: Skill kaldırma
            └── Callback: disabled
```

[Bkz. ORCHESTRATOR.md](ORCHESTRATOR.md) | [Bkz. SKILLS.md](SKILLS.md) | [Bkz. API_REFERENCE.md](API_REFERENCE.md)
