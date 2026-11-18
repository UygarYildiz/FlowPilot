# Project Concept: FlowPilot – AI Operations Platform

FlowPilot, şirketlerin gelen e-postalarını yapay zekâ kullanarak analiz eden, sınıflandıran ve ilgili departmanlara yönlendiren merkezi bir AI destekli operasyon yönetim platformudur.

## Temel Fikir

Bir şirkete gelen tüm e-postalar merkezi bir sistemde toplanır. Sistem, her e-postayı bir Decision Engine aracılığıyla analiz eder.

Decision Engine, e-postanın içeriğini, gönderenini, eklerini ve amacını değerlendirerek aşağıdaki kararları verir:

- E-posta hangi departmanı ilgilendiriyor?
- E-postanın kategorisi ve amacı nedir?
- Hangi işlem yapılmalı?
- Öncelik seviyesi nedir?
- Hangi departman Agent'ı bu e-postayı işlemeli?
- İnsan onayı gerekiyor mu?

Sınıflandırma sonucunda e-posta ilgili departmanın kendi çalışma alanına (inbox) yönlendirilir.

## Departman Bazlı Yapı

Sistem merkezi bir karar mekanizmasına sahip olacak ancak her departmanın kendine ait bağımsız bir Agent'ı ve çalışma alanı bulunacak.

İlk aşamada aşağıdaki departmanları hedefliyoruz:

1. **Procurement (Satın Alma):** Tedarikçi teklifleri, fiyat listeleri, satın alma talepleri, tedarikçi iletişimleri ve teklif karşılaştırmaları.
2. **Sales & Orders (Satış ve Sipariş):** Yeni siparişler, sipariş değişiklikleri, müşteri talepleri, sipariş durum sorguları.
3. **Finance (Finans):** Faturalar, ödeme bildirimleri, tahsilat talepleri, ödeme durumu sorguları.
4. **Logistics (Lojistik):** Sevkiyat talepleri, teslimat gecikmeleri, kargo bilgileri ve teslimat koordinasyonu.

İlerleyen aşamalarda yeni departmanlar ve bunlara ait Agent'lar sisteme kolayca eklenebilmelidir.

## Decision Engine

Decision Engine sistemin merkezi karar mekanizmasıdır.

Yalnızca e-postayı departmanlara ayırmakla kalmaz, e-postanın gerçek amacını da anlamaya çalışır.

Örneğin satın alma departmanına gelen bir e-posta:
- Yeni tedarikçi teklifi olabilir.
- Mevcut siparişin durumu hakkında soru olabilir.
- Fiyat güncellemesi olabilir.
- Tedarikçi şikâyeti olabilir.

Bunların her biri farklı bir işlem gerektirebilir.

Decision Engine yapılandırılmış bir karar üretmeli; departman, kategori, intent, öncelik, güven skoru, önerilen işlem ve gerekli onay bilgilerini belirlemelidir.

Bir e-posta birden fazla departmanı ilgilendirebilir. Bu nedenle sistem gerektiğinde birden fazla departmana yönlendirme yapabilmelidir.

Güven skoru düşük olduğunda veya sınıflandırma belirsiz olduğunda otomatik işlem yapmak yerine e-postayı manuel incelemeye göndermelidir.

## Department Agents

Her departmanın Agent'ı kendi iş alanına ait görevleri yerine getirir.

Agent'lar yalnızca sohbet eden botlar değildir. Gerektiğinde belge okuyabilmeli, veri çıkarabilmeli, şirket içi API'leri kullanabilmeli, ilgili kayıtları sorgulayabilmeli ve iş akışlarını tetikleyebilmelidir.

Örnekler:

- Procurement Agent: Gelen PDF veya Excel tekliflerinden ürün, miktar, fiyat ve teslimat bilgilerini çıkarır. Teklifleri karşılaştırır ve satın alma taslağı hazırlar.
- Orders Agent: Sipariş bilgilerini çıkarır, ürün ve stok kontrolü yapar, sipariş taslağı oluşturur.
- Finance Agent: Fatura bilgilerini analiz eder, ödeme kayıtlarını kontrol eder ve finansal talepleri ilgili süreçlere yönlendirir.
- Logistics Agent: Sevkiyat ve teslimat bilgilerini analiz eder, gecikme durumlarını tespit eder ve lojistik işlemleri için taslaklar hazırlar.

Agent'ların işlem yetkileri birbirinden bağımsız ve kontrollü olmalıdır.

## Merkezi Yönetim Paneli

Platformun temel kullanıcı arayüzü bir operasyon yönetim paneli olacaktır.

Kullanıcılar:

- Gelen tüm e-postaları merkezi inbox üzerinden görebilmeli.
- E-postaların AI tarafından hangi departmana yönlendirildiğini görebilmeli.
- Departmanların kendilerine ait inbox ekranlarını açabilmeli.
- E-postanın orijinal içeriğini ve eklerini görüntüleyebilmeli.
- AI tarafından yapılan sınıflandırmayı, güven skorunu ve gerekçesini inceleyebilmeli.
- İlgili Agent'ın analizini ve önerdiği işlemleri görebilmeli.
- Önerilen işlemleri onaylayabilmeli veya reddedebilmeli.
- Yanlış sınıflandırmaları düzeltebilmeli.
- Geçmiş işlemleri ve Agent faaliyetlerini takip edebilmeli.

## Önemli Tasarım İlkeleri

- Sistem modüler ve genişletilebilir olmalıdır.
- Yeni departmanlar eklemek mevcut departmanların yapısını bozmamalıdır.
- Decision Engine ile departman Agent'ları birbirinden bağımsız sorumluluklara sahip olmalıdır.
- AI'ın yaptığı sınıflandırmalar ve işlemler izlenebilir olmalıdır.
- Kritik işlemler insan onayı olmadan gerçekleştirilmemelidir.
- AI tarafından üretilen bilgiler doğrulama mekanizmalarından geçirilmelidir.
- Belirsiz durumlarda sistem tahmin yürütmek yerine manuel incelemeye başvurmalıdır.
- Hatalı işlemler, tekrar denemeler ve işlem geçmişi yönetilebilir olmalıdır.

## Ürünün Uzun Vadeli Vizyonu

FlowPilot yalnızca e-posta yönlendiren bir araç değildir.

Uzun vadede şirketin farklı departmanları arasında çalışan, gelen talepleri anlayan, doğru iş akışlarını başlatan, departman Agent'ları aracılığıyla operasyonları kolaylaştıran ve insan kontrolünü koruyan merkezi bir AI Operations Platform olmasını hedefliyoruz.

E-posta ilk giriş noktasıdır. Gelecekte ERP olayları, web formları, belgeler ve diğer kurumsal veri kaynakları da sisteme entegre edilebilmelidir.

Ürünün temel amacı, şirket çalışanlarının tekrarlayan operasyonel işlerini azaltmak ve departmanlar arasındaki bilgi akışını daha verimli hâle getirmektir.