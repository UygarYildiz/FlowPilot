# Yol Haritası

FlowPilot artırımlı geliştirilir: her sürüm bir departmanı canlıya alır, uygulama yayındayken bir sonraki departman eklenir.
Kural: Bir sürüm, yayına alınmadan ve DURUM.md'de "tamamlandı" yazmadan bir sonrakine geçilmez.

Durum işaretleri: `[ ]` yapılmadı · `[~]` sürüyor · `[x]` bitti

## v1 — Çekirdek + Procurement
Amaç: Platformun iskeleti ve ilk gerçek ajan canlıda.
- [x] v1 kapsam belgesi (`docs/surumler/v1.md`) — ara hedefler M0–M6 orada
- [x] Teknoloji yığını kararı (ADR-009; LLM: Gemini ücretsiz katman)
- [x] E-posta girişi: seed + IMAP adaptörü, ekler, tekrar önleme (ADR-007) — M1; IMAP yalnızca sahte sunucuyla test edildi
- [x] Decision Engine: departman, kategori, intent, öncelik, güven skoru, çoklu departman — M2
- [x] Ajanı olmayan departmanlar için inbox + manuel işleme — M3
- [~] Departman sözleşmesi (yeni departman = yeni modül, çekirdeğe dokunmadan) — key/name/intents, kayıt defteri (ADR-010), ajan ve öneri tipleri (ADR-014; test departmanı ekle-kaldır testli), salt-okunur araçlar (ADR-015); özel görünümler (`views`) yok, panel genel görünümü kullanıyor
- [x] Merkezi inbox ve departman inbox'ları (panel) — M3; giriş, inceleme kuyruğu, düzeltme
- [x] Onay / ret akışı ve denetim kaydı — M4 (ADR-014): öneri yaşam döngüsü, tek yürütücü (kriter 7 testli), onay bekleyenler, denetim ekranı
- [~] Procurement Agent: PDF/Excel tekliften veri çıkarma, karşılaştırma, satın alma taslağı — 1. parça (`new_quote`, ADR-015) bitti; 2. parça: fiyat güncellemesi, yanıt taslakları, iç talep
- [x] Değerlendirme seti + yönlendirme doğruluğu ölçümü — 150 e-posta; departman %96, otomatik hata %3,1, Procurement intent %100
- [x] Çıkarma seti (30 belge) + ölçüm — alan doğruluğu %98,7, işaretsiz yanlış tutar 0 (kriter 4–5)
- [~] CI/CD ve canlı demo (kurgusal şirket) — CI kuruldu (M0), yayın M6'da

## v2 — Finance
- [ ] Finance Agent: fatura çıkarma (v1'deki belge çıkarmayı yeniden kullanır), ödeme kaydı kontrolü
- [ ] Değerlendirme setine Finance örnekleri; Procurement doğruluğu düşmemeli

## v3 — Sales & Orders
- [ ] Orders Agent: sipariş çıkarma, stok kontrolü, sipariş taslağı

## v4 — Logistics
- [ ] Logistics Agent: sevkiyat bilgisi, gecikme tespiti, lojistik taslakları

## Deneme (v1 içinde, karar bekliyor)
- [x] Karar modelleri (Cloudflare Clef, SubQ Snap 1.2) ile sınıflandırma; Gemini ile karşılaştırma. Seçim: kademeli SubQ → Gemini → insan (ADR-013); test yarısında departman %97,3, otomatik hata %1,5, inceleme %10,8.

## Sonrası (sıralanmadı)
- ERP olayları, web formları ve diğer giriş kaynakları
- n8n / Make gibi iş akışı araçlarına webhook ile tetikleme
