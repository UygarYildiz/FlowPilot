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
150 örnek e-postayla ölçtük (19 Kasım):

| Ne ölçtük | Sonuç | Hedefimiz |
|---|---|---|
| Doğru departmana gönderme | %96 | en az %90 ✅ |
| "Eminim" deyip yanlış gönderme | %3 | en fazla %5 ✅ |
| Satın Alma e-postasının türünü doğru bilme (teklif mi, şikâyet mi…) | %100 | en az %85 ✅ |

Yeni eklenen 94 e-posta bilerek daha zordu: iletilmiş e-postalar, tek satırlık mesajlar, İngilizce
olanlar, yanlış adrese gelenler, iki departman arasında kalanlar, sahte banka e-postası gibi. Sonuçlar
56 e-postalık ilk ölçüme göre biraz düştü (%98 → %96), ki bu beklenen bir şey.

**Yapay zekânın en sık hatası:** gereksiz yere fazladan bir departman eklemek. Örneğin bir tedarikçinin
"ödememizi yapın" hatırlatmasına Finans'ın yanında Satış'ı da eklemiş. Zararı sınırlı: doğru departman
yine e-postayı alıyor, fazladan biri de görüyor.

⚠️ Örneklerin hepsini hâlâ Claude yazdı. Senin yazacağın birkaç gerçekçi e-posta ölçümü daha güvenilir yapar.

## Yol haritası (v1: Çekirdek + Satın Alma)

| Adım | Ne | Durum |
|---|---|---|
| Hazırlık | Proje fikri, kapsam, teknoloji seçimi, belge sistemi | ✅ Bitti |
| M0 | Projenin iskeleti, otomatik testler (GitHub'da her yüklemede çalışır) | ✅ Bitti |
| M1 | E-postaları ve eklerini içeri alma, tekrarları ayıklama | ✅ Bitti |
| M2 | Yapay zekâyla departmana yönlendirme + ölçüm (150 örnek) | ✅ Bitti |
| M3 | **Panel:** e-postaları, kararları ve gerekçelerini ekranda görme, yanlışı düzeltme, giriş | ✅ Bitti |
| M4 | Ajan önerilerini onaylama/reddetme ve tüm sistemin "kim ne yaptı" ekranı | ⬜ Sırada |
| M5 | **Satın Alma ajanı:** tekliften ürün/fiyat çıkarma, teklifleri karşılaştırma, sipariş taslağı | ⬜ |
| M6 | İnternette herkesin açabileceği canlı demo | ⬜ |

v1 bitince sırayla Finans (v2), Satış ve Sipariş (v3), Lojistik (v4) departmanlarının ajanları eklenecek.

## Son oturumlarda ne yaptık?

**19 Kasım — Yapay zekâ yarışı: Gemini, SubQ, Clef**
- Clef ve SubQ Snap 1.2'yi sisteme bağladık, üçünü tarafsız yarıda ölçtük (sonuçlar "Şu an" bölümünde).
- Gemini ile SubQ başa baş çıktı; Clef çok geride kaldı.

**19 Kasım — Örnek seti 150'ye çıktı (M2 bitti)**
- 94 yeni, bilerek daha zor örnek e-posta yazdık; doğru cevaplarını sonuçlara bakmadan belirledik.
- Ölçüm yaptık: üç hedef de tuttu (yukarıdaki tablo). Hataları inceledik ve en sık hatanın "fazladan
  departman eklemek" olduğunu bulduk.

**19 Kasım — Panel (M3)**
- Giriş ekranı ve demo hesapları: yönetici ile Satın Alma, Finans, Satış ve Lojistik çalışanları.
  Her biri yalnızca görmesi gerekeni görüyor; bunu otomatik testlerle de kontrol ediyoruz.
- E-posta listeleri, e-posta ayrıntısı, yönlendirme fişi, düzeltme ve "işlendi" akışı.
- Hepsini tarayıcıda tek tek denedik: giriş, bir departmanın işini kapatma, reklam e-postasını kapatma,
  yanlış yönlendirmeyi düzeltme, telefon ekranı. Bu denemeler senin bilgisayarındaki deneme verisini
  değiştirdi (örn. fuar e-postası kapandı); istersen veriyi sıfırlarız.
- Panel dilini Türkçe yaptık. İngilizceye çevirmek gerekirse metinler tek yerde duruyor.

(Daha eski çalışmalar: `docs/gunluk/`.)

## Şu an
**Üç yapay zekâyı aynı 74 e-postayla yarıştırdık.** Bu yarıya daha önce hiç bakmamıştık, yani sınav
tarafsız. Sonuçlar:

| Ne ölçtük | Gemini (şu anki) | SubQ Snap 1.2 | Clef (küçük) | Clef (büyük) |
|---|---|---|---|---|
| Doğru departmana gönderme | **%97** | %96 | %72 | %77 |
| "Eminim" deyip yanlış gönderme | %0 | %0 | %8 | %0 |
| İki departmanlı e-postada ikisini de bulma | %100 | %100 | %71 | %79 |
| "Bir insan baksın" diye ayırdıkları | **%12** | %30 | %49 | %49 |
| E-posta başına süre | — | 0,3 sn | 0,6 sn | 0,4 sn |

- **SubQ neredeyse Gemini kadar isabetli** ve çok hızlı. Ama emin olmadığında daha sık insana soruyor.
  Örnek: "Sipariş durumumuz ne?" diye soran bir müşteri e-postasında "belki Lojistik de bakmalı" diye
  tereddüt ediyor ve e-postayı insana ayırıyor. Yanlış yere göndermiyor, sadece işi artırıyor.
- SubQ'nun fazla sorması kısmen bizim temkinli bir kuralımızdan geliyordu. Kuralı gevşetmeyi denedik:
  insana ayrılanlar %30'dan %23'e indi, ama bir e-posta yanlış departmana gitti. Kazanç küçük olduğu için
  kuralı değiştirmedik.
- **SubQ'nun olasılıkları dürüst çıktı:** "%50–75 eminim" dediği durumların gerçekten yarısında haklı.
  Yani insana sorduğu e-postalarda gerçekten tereddüt ediyor. Gemini ise neredeyse her zaman "%90+
  eminim" diyor; bu sette çoğunlukla haklı, ama yanıldığında bunu belli etmiyor.
- SubQ'ya soruyu farklı sormayı da denedik: önce "asıl departman hangisi?", sonra "başka departmanın da
  işi var mı?". Daha iyi olmadı, ikinci departmanlarda tereddüt arttı. Eski soru biçiminde kaldık.
- **Clef elendi.** Küçük model, soruları iyileştirdikten sonra da müşteriyi tedarikçiyle karıştırdı.
  Büyük model bu hatayı yapmıyor, ama müşteri e-postalarının çoğuna "bu hiçbir departmanın işi değil"
  diyip insana bırakıyor. Yanlış yere göndermiyor, ama e-postaların yarısını insana bırakıyor.

**Öneri:** Gemini kalsın. SubQ yedek olarak hazırda dursun; Gemini'nin ücretsiz kotası biterse tek ayarla
geçeriz.

## Sırada ne var?
1. **M4 — Onay akışı:** Ajanların önerilerini (ör. "bu tekliften sipariş taslağı hazırladım") onaylama
   veya reddetme ekranı ve bütün sistemin "kim ne yaptı" kaydı.
2. İleride: "fazladan departman" hatasını azaltmak için yapay zekâya verilen talimatı iyileştirmek. Bunu
   yaparken ölçümün kendini kandırmaması için örnek seti ikiye ayıracağız.

## Senden beklenenler
- **Karar:** Hangi yapay zekâ kalsın? Önerim Gemini (SubQ yedekte). Onaylarsan "neden böyle yaptık"
  kaydını yazıp M4'e geçeriz.
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
| Karar modeli | Metin yazmayan, seçeneklere olasılık veren yapay zekâ türü (Cloudflare Clef, SubQ Snap). |
| Ajan | Departmanın işini hazırlayan yapay zekâ (M5'te gelecek). Sadece **önerir**, onay insanındır. |
| Seed | Demo için hazırladığımız kurgusal şirket verisi (Atlas Endüstri). |
| Değerlendirme seti | Doğru cevabını bildiğimiz örnek e-postalar; sistemin ne kadar doğru çalıştığını ölçmek için. |
| ADR | "Neden böyle yaptık" kaydı. `docs/KARARLAR.md`'de durur. |
| CI | GitHub'da her yüklemede testleri otomatik çalıştıran sistem. Yeşil = her şey yolunda. |
