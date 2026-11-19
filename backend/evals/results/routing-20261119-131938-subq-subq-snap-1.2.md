# Yönlendirme değerlendirmesi — subq:subq-snap-1.2

- Tarih: 2026-11-19T13:19:38+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (74 e-posta)
- Prompt: `typed-v2`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %95.9 | ✅ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %0.0 (52 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %97.2 | |
| Çok departmanlı geri çağırma | %100.0 | |
| Manuel incelemeye giden | %29.7 (bunların 19 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.28 sn | |

## Hatalar

- **ev-037** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_status_inquiry', 'logistics': 'shipping_info'}` güven `{'sales_orders': 0.8675, 'logistics': 0.6174}` — Departman olasılıkları: Satış ve Sipariş %87, Lojistik %62, Satın Alma %28, Finans %3
- **ev-100** (inceleme) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'logistics': 'delivery_delay'}` güven `{'logistics': 0.8367}` — Departman olasılıkları: Lojistik %84, Satış ve Sipariş %44, Satın Alma %1, Finans %0
- **ev-111** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'sales_orders': 'customer_request', 'procurement': 'price_update'}` güven `{'sales_orders': 0.6247, 'procurement': 0.5434}` — Departman olasılıkları: Satış ve Sipariş %62, Satın Alma %54, Finans %5, Lojistik %1
- **ev-112** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_change', 'logistics': 'shipment_request'}` güven `{'sales_orders': 0.9812, 'logistics': 0.6662}` — Departman olasılıkları: Satış ve Sipariş %98, Lojistik %67, Satın Alma %1, Finans %0
- **ev-138** (otomatik) beklenen `{'sales_orders': 'customer_request', 'logistics': 'shipment_request'}` → tahmin `{'logistics': 'delivery_issue', 'sales_orders': 'customer_request'}` güven `{'logistics': 0.9565, 'sales_orders': 0.7981}` — Departman olasılıkları: Lojistik %96, Satış ve Sipariş %80, Satın Alma %3, Finans %0
