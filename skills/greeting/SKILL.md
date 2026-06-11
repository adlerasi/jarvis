---
skill_id: greeting-v1
version: "1.0.0"
author: "Adler ASİ"
description: "Selamlama ve sistem durumu sorgulari - karsilama, nabiz yoklama, skill listeleme"
dependencies: []
triggers:
  - keywords: ["merhaba", "selam", "naber", "nasılsın", "hello"]
  - intents: ["greeting", "status_check", "skill_list", "system_info"]
  - patterns:
    - "(naber|nasilsin|nasılsın|merhaba|selam)"
    - "(calisiyor|çalışıyor).*(mu|musun|mısın)"
    - "(skill|beceri|yetenek).*(kac|kaç|tane|sayisi|sayısı)"
    - "(sistem|modul|modül).*(kontrol|dene)"
    - "(hot.?reload|yenile|tazele)"
    - "(jarvis).*(kimsin|nesin|nedir|nasilsin)"
---
