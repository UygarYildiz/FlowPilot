# FlowPilot — Neredeyiz?

> Bu dosya senin için: teknik ayrıntıya girmeden projenin ne durumda olduğunu anlatır.
> Her çalışma oturumunun sonunda güncellenir. Teknik ayrıntı isteyen için: [docs/DURUM.md](docs/DURUM.md).

**Son güncelleme:** 19 Kasım 2026

---

## Proje tek cümlede
Bir şirkete gelen e-postaları yapay zekâyla okuyup doğru departmana gönderen, sonra o departmanın işini
(ör. teklifleri karşılaştırmak) hazırlayıp **insan onayına sunan** bir sistem. İlk departman: Satın Alma.

## Bugün sistem ne yapabiliyor?
Bir örnekle:

1. Kurgusal şirketimiz **Atlas Endüstri**'ye bir tedarikçiden PDF ekli bir fiyat teklifi geliyor.
2. Sistem e-postayı ve ekini kaydediyor, PDF'in içindeki yazıyı okuyor.
   Aynı e-posta ikinci kez gelirse fark ediyor ve iki kez kaydetmiyor.
3. Yapay zekâ (Google Gemini) e-postayı okuyor ve karar veriyor:
   *"Bu Satın Alma'nın işi, bir fiyat teklifi, öncelik normal, %99 eminim."*
4. Bir e-posta iki departmanı ilgilendiriyorsa ikisine de gönderiyor.
   Örnek: *"Eksik ürün geldi ve faturada da hata var"* → hem **Lojistik** hem **Finans**.
5. Emin olmadığında ya da e-posta hiçbir departmanla ilgili değilse (reklam, iş başvurusu…)
   tahmin yürütmüyor, **"bir insan baksın"** diye ayırıyor.

6. **Artık bunların hepsini bir ekranda (panelde) görebiliyorsun:**
   - Yönetici her e-postayı görür. Ayrıca "İnsan baksın" kutusunda yapay zekânın emin olamadıklarını
     bulur; doğru departmana yönlendirir ya da ilgisizse kapatır.
   - Bir departman çalışanı (ör. Satın Alma) yalnızca kendi departmanına gelenleri görür. İşini
     bitirince "İşlendi olarak kapat" der.
   - Her e-postanın yanında bir **yönlendirme fişi** var: hangi departmana gittiği, ne tür bir e-posta
     olduğu, yapay zekânın ne kadar emin olduğu ve nedenini yazdığı gerekçe.
   - Yapay zekâ yanlış yönlendirdiyse düzeltebiliyorsun; düzeltme ve gerekçesi kaydedilir. Kim ne zaman
     ne yaptı, her e-postanın "Geçmiş" bölümünde görünür.

**Henüz olmayanlar:** Satın Alma "ajanı" (teklifleri karşılaştırıp sipariş taslağı hazırlayan kısım) ve
onun önerilerini onaylama/reddetme ekranı. Panel şimdilik yalnızca senin bilgisayarında çalışıyor
(internette değil).

## Ne kadar iyi çalışıyor?
56 örnek e-postayla ölçtük:

| Ne ölçtük | Sonuç | Hedefimiz |
|---|---|---|
| Doğru departmana gönderme | %98 | en az %90 ✅ |
| "Eminim" deyip yanlış gönderme | %2 | en fazla %5 ✅ |
| Satın Alma e-postasının türünü doğru bilme (teklif mi, şikâyet mi…) | %100 | en az %85 ✅ |

⚠️ **Bu sonuçlar olduğundan iyi görünüyor olabilir.** Örnek e-postaların hepsini Claude yazdı;
gerçek hayattaki e-postalar daha dağınık. Hedef 150 e-postaya çıkmak ve senin de birkaç gerçekçi
örnek eklemen.

## Yol haritası (v1: Çekirdek + Satın Alma)

| Adım | Ne | Durum |
|---|---|---|
| Hazırlık | Proje fikri, kapsam, teknoloji seçimi, belge sistemi | ✅ Bitti |
| M0 | Projenin iskeleti, otomatik testler (GitHub'da her yüklemede çalışır) | ✅ Bitti |
| M1 | E-postaları ve eklerini içeri alma, tekrarları ayıklama | ✅ Bitti |
| M2 | Yapay zekâyla departmana yönlendirme + ölçüm | 🔄 Neredeyse bitti (örnek seti 56/150) |
| M3 | **Panel:** e-postaları, kararları ve gerekçelerini ekranda görme, yanlışı düzeltme, giriş | ✅ Bitti |
| M4 | Ajan önerilerini onaylama/reddetme ve tüm sistemin "kim ne yaptı" ekranı | ⬜ Sırada |
| M5 | **Satın Alma ajanı:** tekliften ürün/fiyat çıkarma, teklifleri karşılaştırma, sipariş taslağı | ⬜ |
| M6 | İnternette herkesin açabileceği canlı demo | ⬜ |

v1 bitince sırayla Finans (v2), Satış ve Sipariş (v3), Lojistik (v4) departmanlarının ajanları eklenecek.

## Son oturumlarda ne yaptık?

**19 Kasım — Panel (M3)**
- Giriş ekranı ve demo hesapları: yönetici ile Satın Alma, Finans, Satış ve Lojistik çalışanları.
  Her biri yalnızca görmesi gerekeni görüyor; bunu otomatik testlerle de kontrol ediyoruz.
- E-posta listeleri, e-posta ayrıntısı, yönlendirme fişi, düzeltme ve "işlendi" akışı.
- Hepsini tarayıcıda tek tek denedik: giriş, bir departmanın işini kapatma, reklam e-postasını kapatma,
  yanlış yönlendirmeyi düzeltme, telefon ekranı. Bu denemeler senin bilgisayarındaki deneme verisini
  değiştirdi (örn. fuar e-postası kapandı); istersen veriyi sıfırlarız.
- Panel dilini Türkçe yaptık. İngilizceye çevirmek gerekirse metinler tek yerde duruyor.

**19 Kasım — Bu belge**
- Projeyi kolay takip edebilmen için bu dosyayı yazdık. Her çalışmanın sonunda güncelleniyor; güncellenmezse
  sistem işi bitirmeye ve commit atmaya izin vermiyor.

**19 Kasım — Yapay zekâ kararı (M2)**
- Dört departmanı ve her birinin e-posta türlerini tanımladık (ör. Satın Alma: teklif, fiyat güncellemesi,
  sipariş sorusu, şikâyet, şirket içi talep).
- Gemini'yi bağladık; senin koyduğun anahtarla çalışıyor. Ücretsiz katmanı kullanıyoruz, maliyeti yok.
- Sistemin ne kadar doğru çalıştığını ölçen bir araç yazdık; sonuçlar yukarıda.
- İnternet bir ara koptu ve bir sorunu gösterdi: bağlantı yokken e-postalar yanlışlıkla "insan baksın"
  yığınına düşebilirdi. Düzelttik: artık bağlantı gelince kaldığı yerden devam ediyor.

(Daha eski çalışmalar: `docs/gunluk/`.)

## Sırada ne var?
1. **M4 — Onay akışı:** Ajanların önerilerini (ör. "bu tekliften sipariş taslağı hazırladım") onaylama
   veya reddetme ekranı ve bütün sistemin "kim ne yaptı" kaydı.
2. Örnek e-posta setini 56'dan 150'ye çıkarmak (daha zor, daha dağınık örneklerle). Bu, M4'ten önce de
   yapılabilir; senin tercihin.

## Senden beklenenler
- **Karar:** Sırada M4 mü, yoksa önce örnek seti mi büyütelim?
- **Onay:** Panel Türkçe yapıldı. İlanlar İngilizce ise çevirebiliriz, söylemen yeterli.
- **İsteğe bağlı:** Şirketlere gelebilecek 5–10 gerçekçi e-posta yazarsan ölçüm çok daha güvenilir olur.
  Gerçek kişi/şirket bilgisi koyma; Gemini'nin ücretsiz katmanına yalnızca kurgusal veri gönderiyoruz.

## Kendin denemek istersen
Docker Desktop açıkken, `backend` klasöründe:

```powershell
docker compose up -d
```
```powershell
uv run flowpilot ingest seed
```
```powershell
uv run flowpilot classify
```
```powershell
uv run flowpilot eval routing
```

Sırasıyla: veritabanını başlatır, kurgusal e-postaları içeri alır, yapay zekâya sınıflandırtır, doğruluğu
ölçer. Gerçek Gemini için `backend/.env` içinde `FLOWPILOT_LLM_PROVIDER=gemini` olmalı (şu an `fake`).

**Paneli açmak için** üç şey çalışmalı: veritabanı (yukarıda), API ve panel. `backend` klasöründe:

```powershell
uv run flowpilot users demo
```
```powershell
uv run uvicorn flowpilot.main:app --port 8000
```

Ayrı bir pencerede, `frontend` klasöründe:

```powershell
npm run dev
```

Sonra tarayıcıda http://localhost:5173 adresini aç ve giriş sayfasındaki demo hesaplardan birine tıkla
(şifre otomatik dolar: `flowpilot-demo`).

## Küçük sözlük
| Terim | Anlamı |
|---|---|
| Decision Engine | E-postayı okuyup hangi departmana gideceğine karar veren kısım. |
| Intent | E-postanın amacı: teklif mi, şikâyet mi, sipariş mi… |
| Rota | "Bu e-posta şu departmana gitsin" kararı. Bir e-postanın birden çok rotası olabilir. |
| Güven skoru | Yapay zekânın kararından ne kadar emin olduğu (0–1). 0,75'in altı insana gider. |
| Manuel inceleme | Sistemin emin olamadığı e-postaları bir insanın bakması için ayırdığı yığın. Panelde "İnsan baksın". |
| Yönlendirme fişi | Panelde her e-postanın yanındaki kart: hangi departmana, neden, ne kadar emin. |
| API | Panelin arka planda veri aldığı/gönderdiği kısım. |
| Ajan | Departmanın işini hazırlayan yapay zekâ (M5'te gelecek). Sadece **önerir**, onay insanındır. |
| Seed | Demo için hazırladığımız kurgusal şirket verisi (Atlas Endüstri). |
| Değerlendirme seti | Doğru cevabını bildiğimiz örnek e-postalar; sistemin ne kadar doğru çalıştığını ölçmek için. |
| ADR | "Neden böyle yaptık" kaydı. `docs/KARARLAR.md`'de durur. |
| CI | GitHub'da her yüklemede testleri otomatik çalıştıran sistem. Yeşil = her şey yolunda. |
