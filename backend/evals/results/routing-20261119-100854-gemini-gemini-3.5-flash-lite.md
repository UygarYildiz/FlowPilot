# Yönlendirme değerlendirmesi — gemini:gemini-3.5-flash-lite

- Tarih: 2026-11-19T10:08:54+00:00  ·  Veri seti: `evals/routing/dataset.jsonl` (150 e-posta)
- Prompt: `decision-v1`  ·  Güven eşiği: 0.75

| Ölçüt | Değer | Hedef (v1 bölüm 6) |
|---|---|---|
| 1. Departman doğruluğu | %96.0 | ✅ hedef ≥ %90.0 |
| 2. Otomatik yönlendirilenlerde hata | %3.1 (131 e-posta) | ✅ hedef ≤ %5.0 |
| 3. Procurement intent doğruluğu | %100.0 | ✅ hedef ≥ %85.0 |
| Tüm intent doğruluğu | %98.6 | |
| Çok departmanlı geri çağırma | %96.4 | |
| Manuel incelemeye giden | %12.7 (bunların 17 tanesi aslında doğruydu) | |
| Karar üretilemeyen | 0 | |

## Hatalar

- **ev-047** (otomatik) beklenen `{'logistics': 'delivery_delay'}` → tahmin `{'logistics': 'delivery_delay', 'sales_orders': 'customer_request'}` güven `{'logistics': 0.95, 'sales_orders': 0.9}` — Lojistik firması araç arızası nedeniyle sevkiyatın gecikeceğini bildirmiştir. Bu durum hem lojistik takibini hem de müşteriye bilgi verilmesi için satış operasyonunu ilgilendirmektedir.
- **ev-067** (otomatik) beklenen `{'procurement': 'supplier_complaint'}` → tahmin `{'logistics': 'delivery_issue'}` güven `{'logistics': 0.9}` — Tedarikçi firma, mal kabul rampasındaki uzun beklemelerden şikayetçi ve ek maliyet uyarısı yapıyor.
- **ev-084** (otomatik) beklenen `{'finance': 'payment_status_inquiry'}` → tahmin `{'finance': 'payment_status_inquiry', 'sales_orders': 'customer_request'}` güven `{'finance': 0.95, 'sales_orders': 0.85}` — Tedarikçi vadesi geçmiş ödemenin yapılmadığını ve sevkiyatların durdurulacağını bildiriyor. Bu durum hem finans hem de olası sevkiyat kısıtları nedeniyle satış departmanını ilgilendiriyor.
- **ev-107** (inceleme) beklenen `{'sales_orders': 'customer_request'}` → tahmin `{'sales_orders': 'customer_request', 'logistics': 'delivery_issue'}` güven `{'sales_orders': 0.85, 'logistics': 0.6}` — Müşteri son teslimatta gelen tahrik makaralarından bazılarının ses çıkardığını belirterek teknik inceleme talep ediyor. Bu durum satış sonrası müşteri ilişkileri ve olası ürün değişimi/iadesi kapsamında değerlendirilmelidir.
- **ev-112** (otomatik) beklenen `{'sales_orders': 'order_status_inquiry'}` → tahmin `{'sales_orders': 'order_change'}` güven `{'sales_orders': 0.95}` — Müşteri hem mevcut siparişi için adres değişikliği talep ediyor hem de sevkiyatın ne zaman yapılacağını soruyor, bu nedenle satış departmanının acil olarak ilgilenmesi gerekiyor.
- **ev-126** (otomatik) beklenen `{'logistics': 'delivery_delay'}` → tahmin `{'logistics': 'shipment_request', 'sales_orders': 'order_change'}` güven `{'logistics': 0.9, 'sales_orders': 0.9}` — Üretimdeki arıza nedeniyle SO-2026-0452 siparişinin sevkiyat tarihi ertelenmiştir; hem lojistik hem de satış birimlerinin müşteriye ve nakliyeciye bilgi vermesi gerekmektedir.
- **ev-139** (otomatik) beklenen `{'finance': 'payment_notice', 'sales_orders': 'order_status_inquiry'}` → tahmin `{'finance': 'payment_notice', 'logistics': 'shipment_request'}` güven `{'finance': 0.95, 'logistics': 0.9}` — E-posta hem peşin ödeme bildirimi (finans) hem de bu ödemeye bağlı siparişin sevkiyat zamanını (lojistik) sormaktadır.
- **ev-150** (inceleme) beklenen `{'unknown': None}` → tahmin `{'procurement': 'new_quote'}` güven `{'procurement': 0.4}` — Gönderilen bir teklif e-postasının iletilemediğine dair hata bildirimidir. Satın alma departmanının tedarikçi iletişimini kontrol etmesi gerekir.
