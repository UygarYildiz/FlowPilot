# Yönlendirme değerlendirmesi — cloudflare:clef-flash

- Tarih: 2026-11-19T11:29:35+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (150 e-posta)
- Prompt: `typed-v1`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %72.7 | ❌ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %16.4 (73 e-posta) | ❌ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %97.4 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %96.2 | |
| Çok departmanlı geri çağırma | %53.6 | |
| Manuel incelemeye giden | %51.3 (bunların 48 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |
| Ortanca süre (e-posta başına) | 0.59 sn | |

## Hatalar

- **seed-009** (otomatik) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.8982}` — Departman olasılıkları: Satın Alma %90, Lojistik %20, Satış ve Sipariş %9, Finans %3
- **seed-010** (inceleme) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'procurement': 'order_status_inquiry', 'sales_orders': 'order_change'}` güven `{'procurement': 0.871, 'sales_orders': 0.5676}` — Departman olasılıkları: Satın Alma %87, Satış ve Sipariş %57, Lojistik %16, Finans %2
- **seed-013** (inceleme) beklenen `{'logistics': 'delivery_issue', 'finance': 'invoice_dispute'}` → tahmin `{'procurement': 'supplier_complaint', 'logistics': 'delivery_issue'}` güven `{'procurement': 0.7968, 'logistics': 0.7164}` — Departman olasılıkları: Satın Alma %80, Lojistik %72, Finans %13, Satış ve Sipariş %9
- **ev-021** (inceleme) beklenen `{'procurement': 'supplier_complaint'}` → tahmin `{'procurement': 'supplier_complaint', 'sales_orders': 'order_change'}` güven `{'procurement': 0.8616, 'sales_orders': 0.6701}` — Departman olasılıkları: Satın Alma %86, Satış ve Sipariş %67, Finans %4, Lojistik %4
- **ev-028** (inceleme) beklenen `{'finance': 'payment_notice'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5329}` — Departman olasılıkları: Finans %47, Satın Alma %4, Satış ve Sipariş %2, Lojistik %1
- **ev-033** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.7403}` — Departman olasılıkları: Satın Alma %74, Lojistik %21, Satış ve Sipariş %4, Finans %2
- **ev-034** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.8333}` — Departman olasılıkları: Satın Alma %83, Satış ve Sipariş %30, Finans %3, Lojistik %2
- **ev-036** (inceleme) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'sales_orders': 'order_change', 'logistics': 'shipment_request', 'procurement': 'order_status_inquiry'}` güven `{'sales_orders': 0.9039, 'logistics': 0.8171, 'procurement': 0.7453}` — Departman olasılıkları: Satış ve Sipariş %90, Lojistik %82, Satın Alma %75, Finans %1
- **ev-037** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5491}` — Departman olasılıkları: Satın Alma %45, Lojistik %22, Satış ve Sipariş %10, Finans %1
- **ev-038** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'new_quote'}` güven `{'procurement': 0.9461}` — Departman olasılıkları: Satın Alma %95, Satış ve Sipariş %12, Lojistik %3, Finans %2
- **ev-039** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'new_quote'}` güven `{'procurement': 0.8029}` — Departman olasılıkları: Satın Alma %80, Satış ve Sipariş %14, Finans %1, Lojistik %1
- **ev-040** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5679}` — Departman olasılıkları: Satın Alma %43, Lojistik %6, Satış ve Sipariş %4, Finans %2
- **ev-041** (otomatik) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.9135}` — Departman olasılıkları: Satın Alma %91, Lojistik %17, Satış ve Sipariş %14, Finans %3
- **ev-047** (inceleme) beklenen `{'logistics': 'delivery_delay'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5064}` — Departman olasılıkları: Lojistik %49, Satış ve Sipariş %38, Satın Alma %9, Finans %2
- **ev-048** (inceleme) beklenen `{'finance': 'invoice_received', 'logistics': 'delivery_delay'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.567}` — Departman olasılıkları: Satın Alma %57, Lojistik %37, Finans %25, Satış ve Sipariş %4
- **ev-049** (otomatik) beklenen `{'sales_orders': 'new_order', 'finance': 'invoice_dispute'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.8334}` — Departman olasılıkları: Satın Alma %83, Finans %19, Satış ve Sipariş %17, Lojistik %7
- **ev-058** (otomatik) beklenen `{'procurement': 'new_quote'}` → tahmin `{'procurement': 'price_update'}` güven `{'procurement': 0.879}` — Departman olasılıkları: Satın Alma %88, Satış ve Sipariş %5, Finans %2, Lojistik %1
- **ev-071** (inceleme) beklenen `{'procurement': 'new_quote'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6867}` — Departman olasılıkları: Satın Alma %31, Finans %14, Satış ve Sipariş %8, Lojistik %2
- **ev-091** (inceleme) beklenen `{'finance': 'invoice_received'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6003}` — Departman olasılıkları: Finans %40, Satın Alma %12, Satış ve Sipariş %2, Lojistik %1
- **ev-092** (otomatik) beklenen `{'finance': 'payment_notice'}` → tahmin `{'finance': 'invoice_received'}` güven `{'finance': 0.8427}` — Departman olasılıkları: Finans %84, Satın Alma %9, Satış ve Sipariş %2, Lojistik %2
- **ev-094** (inceleme) beklenen `{'finance': 'invoice_dispute'}` → tahmin `{'finance': 'invoice_received'}` güven `{'finance': 0.6754}` — Departman olasılıkları: Finans %68, Satın Alma %28, Lojistik %22, Satış ve Sipariş %13
- **ev-095** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.715}` — Departman olasılıkları: Satın Alma %72, Lojistik %26, Satış ve Sipariş %12, Finans %3
- **ev-096** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.5681}` — Departman olasılıkları: Satın Alma %57, Lojistik %17, Satış ve Sipariş %5, Finans %3
- **ev-097** (otomatik) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.8599}` — Departman olasılıkları: Satın Alma %86, Satış ve Sipariş %24, Lojistik %16, Finans %2
- **ev-098** (otomatik) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.8041}` — Departman olasılıkları: Satın Alma %80, Lojistik %11, Satış ve Sipariş %11, Finans %2
- **ev-099** (otomatik) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.8546}` — Departman olasılıkları: Satın Alma %85, Satış ve Sipariş %18, Lojistik %4, Finans %1
- **ev-100** (inceleme) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'logistics': 'delivery_delay', 'procurement': 'supplier_complaint'}` güven `{'logistics': 0.8049, 'procurement': 0.5983}` — Departman olasılıkları: Lojistik %80, Satın Alma %60, Satış ve Sipariş %50, Finans %2
- **ev-101** (inceleme) beklenen `{'sales_orders': 'order_change'}` → tahmin `{'procurement': 'purchase_request', 'sales_orders': 'order_change'}` güven `{'procurement': 0.6431, 'sales_orders': 0.6273}` — Departman olasılıkları: Satın Alma %64, Satış ve Sipariş %63, Finans %3, Lojistik %1
- **ev-102** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6476}` — Departman olasılıkları: Satın Alma %35, Satış ve Sipariş %30, Lojistik %7, Finans %1
- **ev-103** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5461}` — Departman olasılıkları: Satın Alma %45, Lojistik %32, Satış ve Sipariş %8, Finans %2
- **ev-104** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'procurement': 'order_status_inquiry'}` güven `{'procurement': 0.6529}` — Departman olasılıkları: Satın Alma %65, Satış ve Sipariş %9, Finans %2, Lojistik %2
- **ev-105** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'price_update'}` güven `{'procurement': 0.8231}` — Departman olasılıkları: Satın Alma %82, Satış ve Sipariş %3, Finans %3, Lojistik %2
- **ev-106** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.6841}` — Departman olasılıkları: Satın Alma %32, Satış ve Sipariş %14, Lojistik %1, Finans %1
- **ev-107** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.8494}` — Departman olasılıkları: Lojistik %15, Satın Alma %15, Satış ve Sipariş %4, Finans %1
- **ev-108** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.631}` — Departman olasılıkları: Satın Alma %63, Satış ve Sipariş %21, Lojistik %13, Finans %1
- **ev-109** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.9199}` — Departman olasılıkları: Satın Alma %92, Lojistik %3, Satış ve Sipariş %3, Finans %2
- **ev-110** (inceleme) beklenen `{'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.9015}` — Departman olasılıkları: Satın Alma %90, Finans %34, Lojistik %8, Satış ve Sipariş %5
- **ev-111** (otomatik) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'procurement': 'price_update'}` güven `{'procurement': 0.8398}` — Departman olasılıkları: Satın Alma %84, Satış ve Sipariş %6, Finans %2, Lojistik %1
- **ev-112** (inceleme) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_change', 'logistics': 'delivery_delay', 'procurement': 'order_status_inquiry'}` güven `{'sales_orders': 0.8254, 'logistics': 0.7268, 'procurement': 0.5397}` — Departman olasılıkları: Satış ve Sipariş %83, Lojistik %73, Satın Alma %54, Finans %1
- **ev-132** (inceleme) beklenen `{'finance': 'payment_notice', 'sales_orders': 'new_order'}` → tahmin `{'procurement': 'purchase_request'}` güven `{'procurement': 0.8475}` — Departman olasılıkları: Satın Alma %85, Satış ve Sipariş %27, Finans %18, Lojistik %12
- **ev-134** (inceleme) beklenen `{'logistics': 'delivery_issue', 'finance': 'invoice_dispute'}` → tahmin `{'finance': 'invoice_dispute'}` güven `{'finance': 0.6149}` — Departman olasılıkları: Finans %61, Lojistik %19, Satın Alma %11, Satış ve Sipariş %3
- **ev-136** (otomatik) beklenen `{'sales_orders': 'order_status_inquiry', 'finance': 'invoice_dispute'}` → tahmin `{'finance': 'invoice_dispute', 'procurement': 'order_status_inquiry'}` güven `{'finance': 0.9115, 'procurement': 0.8185}` — Departman olasılıkları: Finans %91, Satın Alma %82, Lojistik %15, Satış ve Sipariş %9
- **ev-138** (inceleme) beklenen `{'sales_orders': 'customer_request', 'logistics': 'shipment_request'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5266}` — Departman olasılıkları: Satın Alma %47, Lojistik %36, Satış ve Sipariş %4, Finans %1
- **ev-139** (inceleme) beklenen `{'finance': 'payment_notice', 'sales_orders': 'order_status_inquiry'}` → tahmin `{'unknown': None}` güven `{'unknown': 0.5505}` — Departman olasılıkları: Finans %45, Lojistik %40, Satış ve Sipariş %40, Satın Alma %28
