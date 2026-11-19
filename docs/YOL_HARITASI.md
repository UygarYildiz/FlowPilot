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
- [~] Departman sözleşmesi (yeni departman = yeni modül, çekirdeğe dokunmadan) — key/name/intents ve kayıt defteri var (ADR-010); ajan/öneri alanları M4–M5
- [x] Merkezi inbox ve departman inbox'ları (panel) — M3; giriş, inceleme kuyruğu, düzeltme
- [~] Onay / ret akışı ve denetim kaydı — denetim kaydı ve e-posta geçmişi var; öneri onay/ret M4
- [ ] Procurement Agent: PDF/Excel tekliften veri çıkarma, karşılaştırma, satın alma taslağı
- [x] Değerlendirme seti + yönlendirme doğruluğu ölçümü — 150 e-posta; departman %96, otomatik hata %3,1, Procurement intent %100
- [~] CI/CD ve canlı demo (kurgusal şirket) — CI kuruldu (M0), yayın M6'da

## v2 — Finance
- [ ] Finance Agent: fatura çıkarma (v1'deki belge çıkarmayı yeniden kullanır), ödeme kaydı kontrolü
- [ ] Değerlendirme setine Finance örnekleri; Procurement doğruluğu düşmemeli

## v3 — Sales & Orders
- [ ] Orders Agent: sipariş çıkarma, stok kontrolü, sipariş taslağı

## v4 — Logistics
- [ ] Logistics Agent: sevkiyat bilgisi, gecikme tespiti, lojistik taslakları

## Sonrası (sıralanmadı)
- ERP olayları, web formları ve diğer giriş kaynakları
- n8n / Make gibi iş akışı araçlarına webhook ile tetikleme
