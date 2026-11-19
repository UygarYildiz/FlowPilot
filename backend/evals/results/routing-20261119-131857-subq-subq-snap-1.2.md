# Yönlendirme değerlendirmesi — subq:subq-snap-1.2

- Tarih: 2026-11-19T13:18:57+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (76 e-posta)
- Prompt: `typed-v2`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %97.4 | ✅ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %0.0 (56 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %100.0 | |
| Çok departmanlı geri çağırma | %100.0 | |
| Manuel incelemeye giden | %26.3 (bunların 18 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.28 sn | |

## Hatalar

- **ev-062** (inceleme) beklenen `{'procurement': 'price_update'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6008}` — Departman olasılıkları: Satın Alma %40, Finans %1, Satış ve Sipariş %1, Lojistik %0
- **ev-136** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry', 'finance': 'invoice_dispute'}` → tahmin `{'finance': 'invoice_dispute', 'sales_orders': 'order_status_inquiry', 'procurement': 'order_status_inquiry'}` güven `{'finance': 0.9092, 'sales_orders': 0.8534, 'procurement': 0.5812}` — Departman olasılıkları: Finans %91, Satış ve Sipariş %85, Satın Alma %58, Lojistik %16
