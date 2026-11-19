# Yönlendirme değerlendirmesi — subq:subq-snap-1.2

- Tarih: 2026-11-19T14:08:23+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (76 e-posta)
- Prompt: `typed-v3`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %96.1 | ✅ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %0.0 (54 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %100.0 | |
| Çok departmanlı geri çağırma | %92.9 | |
| Manuel incelemeye giden | %28.9 (bunların 19 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.29 sn | |

## Hatalar

- **ev-056** (inceleme) beklenen `{'unknown': None}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.5144}` — Departman olasılıkları: Satın Alma %51, Satış ve Sipariş %12, Lojistik %5, Finans %3
- **ev-062** (inceleme) beklenen `{'procurement': 'price_update'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5643}` — Departman olasılıkları: Satın Alma %44, Satış ve Sipariş %6, Finans %1, Lojistik %0
- **ev-139** (inceleme) beklenen `{'finance': 'payment_notice', 'sales_orders': 'order_status_inquiry'}` → tahmin `{'finance': 'payment_notice', 'logistics': 'shipment_request'}` güven `{'finance': 0.9385, 'logistics': 0.6564}` — Departman olasılıkları: Finans %94, Lojistik %66, Satış ve Sipariş %26, Satın Alma %1
