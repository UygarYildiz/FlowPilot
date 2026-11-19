# Yönlendirme değerlendirmesi — cloudflare:clef-flash

- Tarih: 2026-11-19T13:20:28+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (74 e-posta)
- Prompt: `typed-v2`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %71.6 | ❌ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %7.9 (38 e-posta) | ❌ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %98.2 | |
| Çok departmanlı geri çağırma | %71.4 | |
| Manuel incelemeye giden | %48.6 (bunların 18 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.57 sn | |

## Hatalar

- **seed-010** (inceleme) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'procurement': 'purchase_request', 'sales_orders': 'order_change'}` güven `{'procurement': 0.7916, 'sales_orders': 0.5084}` — Departman olasılıkları: Satın Alma %79, Satış ve Sipariş %51, Lojistik %14, Finans %2
- **seed-013** (inceleme) beklenen `{'logistics': 'delivery_issue', 'finance': 'invoice_dispute'}` → tahmin `{'logistics': 'delivery_issue'}` güven `{'logistics': 0.6358}` — Departman olasılıkları: Lojistik %64, Satın Alma %42, Finans %24, Satış ve Sipariş %5
- **ev-021** (inceleme) beklenen `{'procurement': 'supplier_complaint'}` → tahmin `{'sales_orders': 'order_change', 'procurement': 'supplier_complaint'}` güven `{'sales_orders': 0.608, 'procurement': 0.5028}` — Departman olasılıkları: Satış ve Sipariş %61, Satın Alma %50, Finans %6, Lojistik %5
- **ev-037** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.6625}` — Departman olasılıkları: Satın Alma %66, Satış ve Sipariş %21, Lojistik %19, Finans %2
- **ev-040** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5104}` — Departman olasılıkları: Satın Alma %49, Lojistik %26, Satış ve Sipariş %5, Finans %2
- **ev-041** (otomatik) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.8765}` — Departman olasılıkları: Satın Alma %88, Satış ve Sipariş %13, Lojistik %9, Finans %3
- **ev-048** (inceleme) beklenen `{'finance': 'invoice_received', 'logistics': 'delivery_delay'}` → tahmin `{'finance': 'invoice_received'}` güven `{'finance': 0.902}` — Departman olasılıkları: Finans %90, Satın Alma %37, Lojistik %16, Satış ve Sipariş %4
- **ev-049** (inceleme) beklenen `{'sales_orders': 'new_order', 'finance': 'invoice_dispute'}` → tahmin `{'sales_orders': 'new_order', 'procurement': 'purchase_request'}` güven `{'sales_orders': 0.9166, 'procurement': 0.655}` — Departman olasılıkları: Satış ve Sipariş %92, Satın Alma %66, Finans %43, Lojistik %7
- **ev-077** (inceleme) beklenen `{'finance': 'invoice_received'}` → tahmin `{'finance': 'invoice_received', 'procurement': 'order_status_inquiry'}` güven `{'finance': 0.847, 'procurement': 0.509}` — Departman olasılıkları: Finans %85, Satın Alma %51, Lojistik %3, Satış ve Sipariş %2
- **ev-089** (inceleme) beklenen `{'finance': 'invoice_dispute'}` → tahmin `{'finance': 'invoice_dispute', 'procurement': 'supplier_complaint'}` güven `{'finance': 0.8962, 'procurement': 0.5933}` — Departman olasılıkları: Finans %90, Satın Alma %59, Satış ve Sipariş %4, Lojistik %2
- **ev-091** (inceleme) beklenen `{'finance': 'invoice_received'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.8045}` — Departman olasılıkları: Finans %20, Satın Alma %13, Satış ve Sipariş %3, Lojistik %2
- **ev-095** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.7839}` — Departman olasılıkları: Satın Alma %78, Satış ve Sipariş %28, Lojistik %20, Finans %3
- **ev-096** (otomatik) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.776}` — Departman olasılıkları: Satın Alma %78, Lojistik %11, Satış ve Sipariş %7, Finans %3
- **ev-102** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5692}` — Departman olasılıkları: Satış ve Sipariş %43, Satın Alma %40, Lojistik %7, Finans %2
- **ev-103** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'logistics': 'shipping_info', 'procurement': 'order_status_inquiry'}` güven `{'logistics': 0.5964, 'procurement': 0.5143}` — Departman olasılıkları: Lojistik %60, Satın Alma %51, Satış ve Sipariş %9, Finans %2
- **ev-104** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5601}` — Departman olasılıkları: Satın Alma %44, Satış ve Sipariş %21, Lojistik %8, Finans %4
- **ev-107** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.721}` — Departman olasılıkları: Lojistik %28, Satın Alma %15, Satış ve Sipariş %7, Finans %1
- **ev-110** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.7101}` — Departman olasılıkları: Satın Alma %71, Finans %27, Satış ve Sipariş %11, Lojistik %7
- **ev-111** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'price_update'}` güven `{'procurement': 0.852}` — Departman olasılıkları: Satın Alma %85, Satış ve Sipariş %4, Finans %3, Lojistik %2
- **ev-112** (otomatik) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_change', 'logistics': 'delivery_delay'}` güven `{'sales_orders': 0.912, 'logistics': 0.829}` — Departman olasılıkları: Satış ve Sipariş %91, Lojistik %83, Satın Alma %9, Finans %2
- **ev-138** (inceleme) beklenen `{'sales_orders': 'customer_request', 'logistics': 'shipment_request'}` → tahmin `{'logistics': 'shipment_request'}` güven `{'logistics': 0.8008}` — Departman olasılıkları: Lojistik %80, Satın Alma %31, Satış ve Sipariş %16, Finans %3
- **ev-150** (inceleme) beklenen `{'unknown': None}` → tahmin `{'procurement': 'new_quote'}` güven `{'procurement': 0.5332}` — Departman olasılıkları: Satın Alma %53, Lojistik %4, Satış ve Sipariş %3, Finans %1
