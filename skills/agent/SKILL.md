# Agent Skill — ACA Otonom Ajan

Bu skill, ACA (Autonomous Computer Agent) alt sistemine dogal dil arayuzu saglar.

## Trigger ornekleri

| Intent | Ornek cumle |
|--------|-------------|
| `execute_goal` | "Masaustunde deneme.txt olustur" / "ACA baslat" |
| `get_status` | "ACA durum nedir?" / "Ne yapiyor?" |
| `cancel_goal` | "ACA'yi durdur" / "Iptal et" |
| `approve_step` | "Onayla" / "Devam et" |
| `reject_step` | "Reddet" / "Hayir yapma" |

## Kullanim

```python
from skills.agent import route_agent_request
result = route_agent_request("Masaustunde bir klasor ac", agent_manager)
```
