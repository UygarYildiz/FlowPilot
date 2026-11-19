# Yönlendirme değerlendirmesi — cascade:subq:subq-snap-1.2>gemini:gemini-3.5-flash-lite

- Tarih: 2026-11-19T15:02:23+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (74 e-posta)
- Prompt: `typed-v2>decision-v1`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %97.3 | ✅ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %1.5 (66 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %97.3 | |
| Çok departmanlı geri çağırma | %100.0 | |
| Manuel incelemeye giden | %10.8 (bunların 7 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.28 sn | |
| Kararı veren: `gemini:gemini-3.5-flash-lite` | 16 e-posta, 14 otomatik | |
| Kararı veren: `subq:subq-snap-1.2` | 58 e-posta, 52 otomatik | |

## Hatalar

- **ev-107** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'sales_orders': 'customer_request', 'logistics': 'delivery_issue'}` güven `{'sales_orders': 0.9, 'logistics': 0.85}` — SubQ: Departman olasılıkları: Satış ve Sipariş %59, Lojistik %3, Satın Alma %3, Finans %0
Gemini: Müşteri teslim edilen partideki makaralarda sorun bildirerek teknik inceleme istemektedir. Bu durum hem satış sonrası müşteri memnuniyeti/talebi hem de kusurlu ürün teslimatı kapsamında değerlendirilmelidir.
- **ev-112** (otomatik) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_change'}` güven `{'sales_orders': 0.95}` — SubQ: Departman olasılıkları: Satış ve Sipariş %98, Lojistik %67, Satın Alma %1, Finans %0
Gemini: Müşteri mevcut bir sipariş için adres değişikliği ve sevkiyat tarihi teyidi talep etmektedir.
- **ev-138** (otomatik) beklenen `{'sales_orders': 'customer_request', 'logistics': 'shipment_request'}` → tahmin `{'logistics': 'delivery_issue', 'sales_orders': 'customer_request'}` güven `{'logistics': 0.9565, 'sales_orders': 0.7981}` — Departman olasılıkları: Lojistik %96, Satış ve Sipariş %80, Satın Alma %3, Finans %0
- **ev-150** (inceleme) beklenen `{'unknown': None}` → tahmin `{'procurement': 'new_quote'}` güven `{'procurement': 0.4}` — SubQ: Departman olasılıkları: Satın Alma %9, Finans %1, Lojistik %0, Satış ve Sipariş %0
Gemini: Gönderilen bir teklif e-postasının iletilemediğine dair hata mesajıdır, satın alma süreciyle ilgilidir.
