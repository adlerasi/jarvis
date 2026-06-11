# Feature Specification: Voice Orchestration Layer

**Feature Branch**: `007-voice-orchestration-layer`

**Created**: 2026-06-11

**Status**: Draft

**Input**: User description: "Jarvis hangi modeli kullanırsa kullansın ChatGPT tarzı sesli asistan fonksiyonunu orkestrasyon sağlamalı"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sürekli, Kesintisiz Sesli Sohbet (Priority: P1)

Kullanıcı JARVIS ile doğal bir sohbete başlar. Konuşma akışı kesintisizdir: kullanıcı konuşur, JARVIS anında yanıt verir, kullanıcı JARVIS'in sözünü kesebilir, JARVIS yeni girdiye göre yanıtını günceller. Arka uç (Gemini veya Ollama) değişse bile bu deneyim aynı kalır.

**Why this priority**: Sesli asistanın temel değer önerisi budur. Kullanıcı deneyimini doğrudan belirler.

**Independent Test**: Kullanıcı "bugün hava nasıl?" diye sorar, yanıt bekler, yanıt tamamlanmadan "takvimimi göster" der. Sistem ikinci komutu alır, birinciyi bırakır ve yeni yanıtı üretir.

**Acceptance Scenarios**:

1. **Given** JARVIS dinleme modundayken, **When** kullanıcı bir soru sorar, **Then** JARVIS 3 saniye içinde yanıt vermeye başlar
2. **Given** JARVIS bir yanıt okurken, **When** kullanıcı yeni bir şey söyler, **Then** JARVIS mevcut yanıtı durdurur ve yeni girdiyi işler
3. **Given** kullanıcı 30 saniye boyunca sessiz kalırken, **When** hiçbir şey söylemez, **Then** JARVIS dinleme modunda kalmaya devam eder, hata durumuna geçmez

---

### User Story 2 - Arka Uç Değişse Bile Aynı Deneyim (Priority: P1)

Kullanıcı ayarlardan Gemini'den Ollama'ya geçiş yapar. Konuşma akışı, durum göstergeleri, araya girme özelliği ve hata yönetimi aynı şekilde çalışır. Sadece yanıt hızı ve kalitesi değişir.

**Why this priority**: Çift arka uç desteği projenin temel mimari kararıdır. Her iki backendi de aynı kullanıcı deneyimini sunmalıdır.

**Independent Test**: Ayarlardan backend "ollama" olarak değiştirilir. Kullanıcı "merhaba" der. Sistem "merhaba" yanıtını verir, UI durumu LISTENING'e döner. Ardından backend "gemini"ye alınır, aynı test tekrarlanır.

**Acceptance Scenarios**:

1. **Given** backend Gemini iken, **When** kullanıcı Ollama'ya geçer, **Then** sistem yeni backend'i yükler ve dinleme moduna geçer, hata vermez
2. **Given** Ollama backend'inde kullanıcı bir soru sorarken, **When** soru tamamlanır, **Then** UI sırasıyla LISTENING → THINKING → SPEAKING durumlarını gösterir
3. **Given** Gemini backend'inde aynı senaryo, **When** aynı adımlar tekrarlanır, **Then** UI aynı durum geçişlerini gösterir

---

### User Story 3 - Hata Sonrası Kendini Kurtarma (Priority: P2)

Bağlantı kopması, backend hatası veya beklenmeyen bir durum oluştuğunda sistem çökmez, kullanıcıya durumu bildirir ve otomatik olarak yeniden bağlanmaya çalışır.

**Why this priority**: Kullanıcının asistanı sık sık yeniden başlatmak zorunda kalmaması için kritiktir.

**Independent Test**: Backend bağlantısı kesilir (örneğin Gemini API geçici olarak kullanılamaz). Sistem hata durumuna geçer, kullanıcıya bildirim gösterir ve 3 saniye içinde yeniden bağlanmayı dener.

**Acceptance Scenarios**:

1. **Given** JARVIS çalışırken, **When** backend bağlantısı kopar, **Then** UI hata durumuna geçer ve kullanıcıya "Bağlantı hatası" mesajı gösterilir
2. **Given** bağlantı hatası oluşmuşken, **When** 3 saniye beklenir, **Then** sistem otomatik olarak yeniden bağlanmayı dener
3. **Given** STT (ses tanıma) art arda 3 kez hata verirken, **When** 4. hata oluşur, **Then** STT durdurulur ve kullanıcıya "Ses tanıma sürekli hata veriyor" uyarısı gösterilir

---

### Edge Cases

- Kullanıcı çok hızlı art arda komut verdiğinde her komut sırayla işlenir, hiçbiri kaybolmaz
- Ses seviyesi çok düşük olduğunda (fısıltı) sistem sessizliği atlar, yanlış tetikleme yapmaz
- Kullanıcı tam JARVIS yanıt verirken "dur" dediğinde ses çıkışı durar, yeni bir dinleme döngüsü başlar
- Tüm arka uçlar kullanılamaz durumda olduğunda UI bunu net bir şekilde gösterir, batık döngüye girmez

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sesli asistan, hangi backend (Gemini veya Ollama) kullanılırsa kullanılsın, aynı temel kullanıcı deneyimini sağlamalıdır: dinleme, düşünme, konuşma ve araya girme
- **FR-002**: Kullanıcı JARVIS konuşurken araya girdiğinde, sistem mevcut ses çıkışını durdurmalı, yeni ses girdisini işleme almalı ve yanıtı buna göre güncellemelidir
- **FR-003**: UI durum makinesi (LISTENING → THINKING → SPEAKING → LISTENING) tüm durum geçişlerini merkezi olarak yönetmeli ve geçersiz geçişleri engellemelidir
- **FR-004**: Tüm hata durumlarında UI state'i `set_state()` üzerinden geçmelidir, asla doğrudan `ui.set_state()` çağrılmamalıdır
- **FR-005**: Ses çıkış kuyruğu sınırlandırılmalıdır, sınırsız büyüme engellenmelidir
- **FR-006**: Ses girdi işleme (mikrofon) asla bloke olmamalıdır; JARVIS konuşurken bile mikrofon verisi okunmaya devam etmelidir
- **FR-007**: Backend bağlantısı koptuğunda sistem otomatik olarak yeniden bağlanmayı denemeli, maksimum 3 denemeden sonra kullanıcıya bildirim göstermelidir
- **FR-008**: Ses seviyesi eşik değerinin altındaki girdiler (fısıltı, ortam gürültüsü) backend'e gönderilmemeli, sessizce atlanmalıdır

### Key Entities

- **JarvisLive (JARVIS Çekirdeği)**: Tüm orkestrasyonun merkezi. Provider'ları başlatır/durdurur, state yönetimini yapar, hata kurtarmayı yönetir.
- **Provider (Backend Adaptörü)**: Gemini veya Ollama arka ucunu sarmalayan soyutlama. Ortak arayüz üzerinden sesli konuşma döngüsünü çalıştırır.
- **UI State Machine**: Kullanıcıya görsel geri bildirim sağlayan durum makinesi. Geçiş kurallarını merkezi olarak tanımlar.
- **Audio Pipeline**: Ses girdisi (mikrofon) ve ses çıktısı (hoparlör) arasındaki veri akışını yöneten boru hattı. Amplitude gate, kuyruk yönetimi, barge-in içerir.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Kullanıcı JARVIS konuşurken araya girdiğinde, mevcut ses çıkışı 500ms içinde durur ve yeni girdi işlenmeye başlar
- **SC-002**: Her iki backend'de de (Gemini ve Ollama) UI durum geçişleri LISTENING → THINKING → SPEAKING sırasını tutarlı şekilde gösterir
- **SC-003**: Backend bağlantı hatası sonrası sistem 5 saniye içinde yeniden bağlanma denemesi başlatır
- **SC-004**: Ses çıkış kuyruğu maksimum 10 saniyelik (≈160KB) tampon ile sınırlanır, aşıldığında en eski veri atılır
- **SC-005**: Hata durumuna geçildiğinde UI state'i merkezi `set_state()` üzerinden güncellenir, doğrudan `ui.set_state` çağrısı kalmaz

## Assumptions

- Mikrofon verisi JARVIS konuşurken de okunmaya devam eder (FR-006), sadece backend'e iletimi durur
- Ollama backend'i gerçek zamanlı ses akışı yerine istek-cevap modeli kullandığı için araya girme deneyimi Gemini'den farklı olabilir; ancak state yönetimi ve hata kurtarma aynı olmalıdır
- Kullanıcı araya girdiğinde Gemini Live API'nin turn management mekanizması kullanılacaktır; Ollama için ayrı bir turn yönetimi gerekecektir
- Ses çıkış kuyruğu için `asyncio.Queue(maxsize=N)` yeterlidir; overflow durumunda en eski chunk atılır

