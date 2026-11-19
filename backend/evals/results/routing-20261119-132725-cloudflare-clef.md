# Yönlendirme değerlendirmesi — cloudflare:clef

- Tarih: 2026-11-19T13:27:25+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (74 e-posta)
- Prompt: `typed-v2`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %77.0 | ❌ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %0.0 (38 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %98.3 | |
| Çok departmanlı geri çağırma | %78.6 | |
| Manuel incelemeye giden | %48.6 (bunların 19 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.42 sn | |

## Hatalar

- **seed-013** (inceleme) beklenen `{'logistics': 'delivery_issue', 'finance': 'invoice_dispute'}` → tahmin `{'procurement': 'supplier_complaint', 'finance': 'invoice_dispute', 'logistics': 'delivery_issue'}` güven `{'procurement': 0.7674, 'finance': 0.7064, 'logistics': 0.5154}` — Departman olasılıkları: Satın Alma %77, Finans %71, Lojistik %52, Satış ve Sipariş %27
- **ev-021** (inceleme) beklenen `{'procurement': 'supplier_complaint'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5517}` — Departman olasılıkları: Satın Alma %45, Satış ve Sipariş %34, Finans %7, Lojistik %2
- **ev-037** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.7085}` — Departman olasılıkları: Satın Alma %29, Lojistik %25, Satış ve Sipariş %18, Finans %2
- **ev-040** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.7907}` — Departman olasılıkları: Satış ve Sipariş %21, Finans %3, Lojistik %2, Satın Alma %1
- **ev-041** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5701}` — Departman olasılıkları: Satın Alma %43, Satış ve Sipariş %14, Lojistik %8, Finans %5
- **ev-045** (inceleme) beklenen `{'logistics': 'shipping_info'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5034}` — Departman olasılıkları: Lojistik %50, Satış ve Sipariş %3, Finans %1, Satın Alma %1
- **ev-048** (inceleme) beklenen `{'finance': 'invoice_received', 'logistics': 'delivery_delay'}` → tahmin `{'procurement': 'order_status_inquiry', 'finance': 'invoice_received'}` güven `{'procurement': 0.8716, 'finance': 0.8523}` — Departman olasılıkları: Satın Alma %87, Finans %85, Lojistik %29, Satış ve Sipariş %2
- **ev-049** (inceleme) beklenen `{'sales_orders': 'new_order', 'finance': 'invoice_dispute'}` → tahmin `{'sales_orders': 'new_order'}` güven `{'sales_orders': 0.9561}` — Departman olasılıkları: Satış ve Sipariş %96, Finans %50, Lojistik %10, Satın Alma %2
- **ev-094** (inceleme) beklenen `{'finance': 'invoice_dispute'}` → tahmin `{'finance': 'invoice_dispute', 'procurement': 'supplier_complaint'}` güven `{'finance': 0.9062, 'procurement': 0.6153}` — Departman olasılıkları: Finans %91, Satın Alma %62, Satış ve Sipariş %8, Lojistik %1
- **ev-096** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.51}` — Departman olasılıkları: Satış ve Sipariş %49, Lojistik %20, Satın Alma %11, Finans %3
- **ev-102** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5259}` — Departman olasılıkları: Satış ve Sipariş %47, Satın Alma %7, Lojistik %3, Finans %2
- **ev-103** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6077}` — Departman olasılıkları: Lojistik %39, Satış ve Sipariş %34, Satın Alma %20, Finans %2
- **ev-104** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.693}` — Departman olasılıkları: Satış ve Sipariş %31, Satın Alma %20, Finans %3, Lojistik %2
- **ev-107** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.8149}` — Departman olasılıkları: Satış ve Sipariş %19, Satın Alma %5, Lojistik %2, Finans %1
- **ev-110** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6685}` — Departman olasılıkları: Satış ve Sipariş %33, Satın Alma %17, Finans %11, Lojistik %1
- **ev-111** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6513}` — Departman olasılıkları: Satın Alma %35, Satış ve Sipariş %20, Finans %2, Lojistik %1
- **ev-112** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_change', 'logistics': 'shipment_request'}` güven `{'sales_orders': 0.929, 'logistics': 0.5912}` — Departman olasılıkları: Satış ve Sipariş %93, Lojistik %59, Satın Alma %2, Finans %1
- **ev-133** (inceleme) beklenen `{'logistics': 'delivery_delay', 'finance': 'invoice_received'}` → tahmin `{'finance': 'invoice_received'}` güven `{'finance': 0.9156}` — Departman olasılıkları: Finans %92, Lojistik %47, Satın Alma %21, Satış ve Sipariş %1
