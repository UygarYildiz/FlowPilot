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
3. Yapay zekâ e-postayı okuyor ve karar veriyor. Önce ucuz ve hızlı model (SubQ) bakıyor; emin değilse
   daha güçlü model (Google Gemini) bakıyor; o da emin değilse e-posta insana gidiyor:
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

7. **Onay akışı hazır (yeni):** Bir departmanın "ajanı" bir iş hazırladığında (ör. *"Özkan Rulman
   teklifini kaydet: 3 kalem, 18.450 TL"*) bu bir **öneri** olarak e-postanın yanında görünür.
   - Yetkili kişi **"Onayla ve uygula"** der ya da gerekçe yazarak **reddeder**.
   - Onaylanan öneri **tam bir kez** uygulanır; iki kişi aynı anda bassa bile. Reddedilen hiçbir zaman
     uygulanmaz. Uygulama sırasında hata olursa öneri "Uygulanamadı" olur ve "Yeniden dene" denebilir.
   - Menüde **"Onay bekleyenler"** listesi var. Yönetici için **"Denetim kaydı"** ekranı: sistemde kim,
     ne zaman, ne yaptı; en yeniden eskiye, aranabilir.

**Henüz olmayanlar:** Satın Alma ajanının kendisi (teklifleri okuyup karşılaştıran kısım, M5). Yani onay
akışı hazır ama ona öneri gönderecek gerçek ajan henüz yok. Panel şimdilik yalnızca senin bilgisayarında
çalışıyor (internette değil).

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
| M4 | Ajan önerilerini onaylama/reddetme ve tüm sistemin "kim ne yaptı" ekranı | ✅ Bitti |
| M5 | **Satın Alma ajanı:** tekliften ürün/fiyat çıkarma, teklifleri karşılaştırma, sipariş taslağı | ⬜ Sırada |
| M6 | İnternette herkesin açabileceği canlı demo | ⬜ |

v1 bitince sırayla Finans (v2), Satış ve Sipariş (v3), Lojistik (v4) departmanlarının ajanları eklenecek.

## Son oturumlarda ne yaptık?

**19 Kasım — Onay akışı (M4 bitti)**
- Departmanların "ajan" takabileceği kurallar yazıldı: ajan yalnızca öneri hazırlar, hiçbir şeyi kendisi
  değiştiremez.
- Öneriler onaylanır ya da gerekçeyle reddedilir; onaylanan tam bir kez uygulanır. Bunu, iki işlemin
  aynı öneriyi aynı anda uygulamaya çalıştığı bir test dahil, otomatik testlerle kanıtladık.
- Panele "Onay bekleyenler" listesi, e-postada "Ajan önerileri" bölümü ve yönetici için "Denetim kaydı"
  ekranı eklendi; hepsini tarayıcıda denedik.

**19 Kasım — Yapay zekâ yarışı ve yeni düzen**
- Clef ve SubQ'yu sisteme bağladık, Gemini ile tarafsız yarıda yarıştırdık; Clef elendi.
- SubQ'nun neden fazla insana sorduğunu inceledik: model dürüst, sınırdaki e-postalarda gerçekten tereddüt ediyor.
- Önce SubQ, sonra Gemini, sonra insan düzenini kurduk ve gerçek ölçümle doğruladık (sonuçlar "Şu an" bölümünde).

**19 Kasım — Örnek seti 150'ye çıktı (M2 bitti)**
- 94 yeni, bilerek daha zor örnek e-posta yazdık; doğru cevaplarını sonuçlara bakmadan belirledik.
- Ölçüm yaptık: üç hedef de tuttu (yukarıdaki tablo). Hataları inceledik ve en sık hatanın "fazladan
  departman eklemek" olduğunu bulduk.

(Daha eski çalışmalar: `docs/gunluk/`.)

## Şu an
**M4 bitti: onay akışı hazır.** Yapay zekâ seçimi de kapandı: önce SubQ, emin değilse Gemini, o da emin
değilse insan (ayrıntılar `docs/KARARLAR.md`, ADR-013).

Tarayıcıda denerken onay ekranını görebilmek için bilgisayarındaki deneme verisine, geçici bir deneme
ajanıyla üç öneri ekledik ("SAT-2026-031 talebiniz için fiyat teklifimiz" e-postasında): biri uygulandı,
biri reddedildi, biri "Uygulanamadı" durumunda (deneme ajanı artık sistemde olmadığı için). Bunlar ve
denetim kayıtları deneme verisinde duruyor; istersen M6'daki "veriyi sıfırla" ile temizlenir.

## Sırada ne var?
1. **M5 — Satın Alma ajanı:** teklif PDF/Excel'inden tedarikçi, ürün, miktar ve fiyatları çıkarmak;
   aynı talebe gelen teklifleri karşılaştırmak; satın alma taslağını öneri olarak onaya sunmak. Çıkarılan
   sayıların doğruluğunu ölçmek için ayrı bir örnek seti de hazırlanacak.
2. İleride: "fazladan departman" hatasını azaltmak için yapay zekâya verilen talimatı iyileştirmek.

## Senden beklenenler
- **Bilgi:** Bilgisayarındaki ayarı yeni düzene çevirdim; artık gerçek Gemini kullanılıyor (önceden sahte
  bir model ayarlıydı). Gemini'ye yalnızca kurgusal veri gönderiyoruz.
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
ölçer. Ayar `backend/.env` içinde: `FLOWPILOT_DECISION_ENGINE=cascade` (önce SubQ, sonra Gemini) ve
`FLOWPILOT_LLM_PROVIDER=gemini`. Sahte modele dönmek için ikincisini `fake` yap.

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
| Kademeli yönlendirme | Önce ucuz model bakar, emin değilse güçlü model, o da emin değilse insan. |
| Ajan | Departmanın işini hazırlayan yapay zekâ (ilki M5'te). Sadece **önerir**, onay insanındır. |
| Öneri | Ajanın hazırladığı iş (ör. "bu teklifi kaydet"). Onaylanınca bir kez uygulanır, reddedilirse hiç. |
| Denetim kaydı | Sistemde olan her şeyin silinemeyen listesi: kim, ne zaman, ne yaptı. |
| Seed | Demo için hazırladığımız kurgusal şirket verisi (Atlas Endüstri). |
| Değerlendirme seti | Doğru cevabını bildiğimiz örnek e-postalar; sistemin ne kadar doğru çalıştığını ölçmek için. |
| ADR | "Neden böyle yaptık" kaydı. `docs/KARARLAR.md`'de durur. |
| CI | GitHub'da her yüklemede testleri otomatik çalıştıran sistem. Yeşil = her şey yolunda. |
