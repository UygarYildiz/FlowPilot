# Yönlendirme değerlendirmesi — gemini:gemini-3.5-flash-lite

- Tarih: 2026-11-18T23:38:08+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (56 e-posta)
- Prompt: `decision-v1`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %98.2 | ✅ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %2.1 (48 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %100.0 | |
| Çok departmanlı geri çağırma | %100.0 | |
| Manuel incelemeye giden | %14.3 (bunların 8 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |

## Hatalar

- **ev-047** (otomatik) beklenen `{'logistics': 'delivery_delay'}` → tahmin `{'logistics': 'delivery_delay', 'sales_orders': 'order_status_inquiry'}` güven `{'logistics': 0.95, 'sales_orders': 0.85}` — Nakliye firması sevkiyatın arıza nedeniyle yarına kaldığını bildirmektedir. Bu durum lojistik takibini ve müşteri sipariş durumunu doğrudan ilgilendirmektedir.
