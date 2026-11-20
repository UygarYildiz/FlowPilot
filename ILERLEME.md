# FlowPilot — Neredeyiz?

> Bu dosya senin için: teknik ayrıntıya girmeden projenin ne durumda olduğunu anlatır.
> Her çalışma oturumunun sonunda güncellenir. Teknik ayrıntı isteyen için: [docs/DURUM.md](docs/DURUM.md).

**Son güncelleme:** 20 Kasım 2026

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

7. **Onay akışı:** Bir departmanın "ajanı" bir iş hazırladığında bu bir **öneri** olarak e-postanın
   yanında görünür.
   - Yetkili kişi **"Onayla ve uygula"** der ya da gerekçe yazarak **reddeder**.
   - Onaylanan öneri **tam bir kez** uygulanır; iki kişi aynı anda bassa bile. Reddedilen hiçbir zaman
     uygulanmaz. Uygulama sırasında hata olursa öneri "Uygulanamadı" olur ve "Yeniden dene" denebilir.
   - Menüde **"Onay bekleyenler"** listesi var. Yönetici için **"Denetim kaydı"** ekranı: sistemde kim,
     ne zaman, ne yaptı; en yeniden eskiye, aranabilir.

8. **Satın Alma ajanı teklifleri okuyor (yeni):** Bir tedarikçi teklif gönderdiğinde (PDF, Excel ya
   da CSV) ajan eki okuyor ve iki öneri hazırlıyor:
   - *"Özkan Rulman teklifini kaydet: 3 kalem, 106.672,80 TRY"*: tedarikçi, teklif no, geçerlilik,
     satırlar (ürün, miktar, birim fiyat, tutar, teslim süresi) ve toplamlar.
   - Aynı talebe başka teklif de varsa: *"SAT-2026-031 için satın alma taslağı: 3 kalem, 80.944,50 TRY"*.
     Farklı para birimlerini sabit bir demo kuruyla TL'ye çevirip her ürün için en ucuzunu seçiyor ve
     nedenini yazıyor (ör. "en ucuz ama teslim süresi daha uzun: 21 gün"). Seçim yine senin.
   - **Ajan sayı uydurmuyor:** Çıkardığı her sayının belgede gerçekten yazıp yazmadığını ve toplamların
     tutup tutmadığını kendisi kontrol ediyor. Tutmayan değeri düzeltmeye çalışmıyor, panelde kırmızıyla
     "şüpheli" diye gösteriyor.

9. **Satın Alma ajanı diğer e-postaları da işliyor (yeni):**
   - **Fiyat güncellemesi:** *"Kaya Hidrolik fiyatlarını güncelle — 4 ürün: 3 zam (ort. %8,6), 1
     değişmedi"*. Önceki fiyatı önce kayıtlarımızdan, yoksa belgedeki "eski fiyat"tan alıyor ve hangisini
     kullandığını yazıyor.
   - **Sipariş durumu sorusu ve tedarikçi şikâyeti:** özet, öncelik önerisi ve bir **yanıt taslağı**.
     Ajan önce e-postadaki sipariş/talep numaralarını kayıtlarda arıyor; bulamazsa taslakta bunu
     dürüstçe söylüyor ("kontrol edip dönüş yapacağız"), tarih ya da söz uydurmuyor. Taslakta e-postada
     ve kayıtlarda olmayan bir sayı geçerse uyarı veriyor. **Hiçbir e-posta gönderilmiyor**; onay yalnızca
     taslağı kaydediyor.
   - **Şirket içi satın alma talebi:** *"Satın alma talebi oluştur: 3 kalem (Üretim Planlama, en geç
     24.11.2026)"*. Onaylanınca talep numarası veriliyor (SAT-2026-101, 102…).

10. **Sistem artık kendiliğinden çalışabiliyor (yeni):** Bir "işleyici" posta kutusuna sürekli bağlı
    duruyor. Kutuya yeni e-posta düştüğü an posta sunucusu haber veriyor; işleyici e-postayı çekiyor,
    yönlendiriyor, ajanı çalıştırıyor ve öneriyi panele koyuyor. Kimsenin komut çalıştırması gerekmiyor.
    Posta kutusunda hiçbir şeyi değiştirmiyor ("okundu" işareti bile koymuyor). Bağlantı koparsa kendisi
    yeniden bağlanıyor; yapay zekâya o an ulaşamazsa birkaç dakika sonra yeniden deniyor.
    ⚠️ Bunu şimdilik yalnızca sahte bir posta sunucusuyla denedik; gerçek Gmail denemesi seni bekliyor.

**Henüz olmayanlar:** Finans, Satış ve Lojistik departmanlarının ajanları (v2–v4). Panel şimdilik yalnızca
senin bilgisayarında çalışıyor (internette değil).

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

**Tekliften bilgi çıkarma** — 30 kurgusal teklif belgesiyle ölçtük (20 Kasım). Belgeler 6 farklı
düzende (PDF tablo, PDF düz yazı, iki Excel ve iki CSV biçimi), TL/EUR/USD, ve bilerek tuzaklı: para
birimi yazılmamış, teslim süresi hafta olarak, tedarikçi satır tutarını yanlış yazmış, genel toplam
tutmuyor, miktarsız teklif, teklif olmayan bir irsaliye.

| Ne ölçtük | Sonuç | Hedefimiz |
|---|---|---|
| Alanları doğru okuma (762 alan) | %98,7 | en az %90 ✅ |
| Fark edilmeden geçen yanlış tutar | 0 | 0 ✅ |
| Tutarları doğru okuma | %100 | |
| Teklif olanı olmayandan ayırma | %100 | |

Kalan hataların hepsi aynı türden: yapay zekâ bazı belgelerde teslim süresini boş bıraktı (tutar değil).
Tuzaklı belgelerdeki sorunların hepsini kontrol yakaladı ve "şüpheli" diye işaretledi.

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
| M5 | **Satın Alma ajanı:** tekliften ürün/fiyat çıkarma, teklifleri karşılaştırma, sipariş taslağı | ✅ Bitti |
| M6 | Gerçek posta kutusuyla otomatik çalışma, sonra internette canlı demo | ⬜ Sırada |

v1 bitince sırayla Finans (v2), Satış ve Sipariş (v3), Lojistik (v4) departmanlarının ajanları eklenecek.

## Son oturumlarda ne yaptık?

**20 Kasım — Kendiliğinden çalışan sistem (M6, 1. parça)**
- Senin isteğinle yayını sonraya bıraktık: önce sistem gerçek bir ürün gibi kendi başına çalışmalı.
- "İşleyici" yazıldı (yukarıda 10. madde): posta kutusuna bağlı kalıyor, yeni e-posta gelince hemen
  işliyor. Her e-postanın gelişinden öneriye kaç saniye sürdüğünü ölçen bir komut da eklendi.
- Sahte posta sunucusuyla otomatik testleri geçti. Gerçek Gmail'le deneme sırada.

**20 Kasım — Satın Alma ajanı, 2. parça (M5 bitti)**
- Fiyat güncellemesi, sipariş durumu sorusu, tedarikçi şikâyeti ve iç satın alma talebi e-postaları da
  artık öneriye dönüşüyor (yukarıda 9. madde).
- Kurgusal şirketin dört gerçek e-postasıyla gerçek yapay zekâyı denedik: hepsi doğru öneri üretti,
  yanıt taslakları hiçbir şey uydurmadı. Şikâyet yanıtını tarayıcıda onayladık (gönderilmedi).

**20 Kasım — Satın Alma ajanı, 1. parça (M5)**
- Ajan teklif eklerini okuyor, sayıları belgeye ve aritmetiğe karşı kontrol ediyor, "teklifi kaydet" ve
  "satın alma taslağı" öneriyor. 30 belgelik ölçüm setinde iki hedef de tuttu.

(Daha eski çalışmalar: `docs/gunluk/`.)

## Şu an
**M6, 1. parça:** sistemin gerçek bir posta kutusuyla kendi başına çalışması. İşleyici yazıldı ve testlerden
geçti; gerçek Gmail kutusuyla deneme senin hesabını bekliyor.

Bilgisayarındaki deneme verisinde seni bekleyen üç öneri hâlâ duruyor (menüde "Onay bekleyenler").

## Sırada ne var?
1. **Gerçek deneme:** sen test Gmail hesabını bağlarsın, işleyiciyi açarız, kendi hesabından ona kurgusal
   Atlas e-postaları (ekli teklifler dahil) gönderirsin; birkaç saniye içinde panelde görünmeleri gerekir.
   "Gelişten öneriye 60 saniyenin altında" hedefini burada ölçeceğiz.
2. Sonra: demo hesabı, "demo verisini sıfırla", README ve tanıtım, internete koyma (M6'nın geri kalanı).
3. **Sonraya not:** panelden "posta kutunu bağla" (her şirket kendi kutusunu bağlasın) v1'de yok: bu, şifreleri
   güvenle saklamayı ve birden çok şirketi ayırmayı gerektiriyor. v1'de kutu ayar dosyasından bağlanıyor.

## Senden beklenenler
- **Test posta kutusu:** yeni bir Gmail hesabı aç (kendi hesabın değil), iki adımlı doğrulamayı aç ve bir
  "uygulama şifresi" al (Google Hesabı → Güvenlik → Uygulama şifreleri). `backend/.env` dosyasına sen yaz;
  ben şifre girmiyorum: `FLOWPILOT_IMAP_HOST=imap.gmail.com`, `FLOWPILOT_IMAP_USER=<yeni adres>`,
  `FLOWPILOT_IMAP_PASSWORD=<16 haneli uygulama şifresi>`. Kendi hesabın olmamasının nedeni: Gemini'nin
  ücretsiz katmanına yalnızca kurgusal veri gönderiyoruz.
- **Onay:** Panel Türkçe yapıldı. İlanlar İngilizce ise çevirebiliriz, söylemen yeterli.
- **İsteğe bağlı:** Şirketlere gelebilecek 5–10 gerçekçi e-posta yazarsan ölçüm çok daha güvenilir olur.
  Gerçek kişi/şirket bilgisi koyma.

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

**Posta kutusunu izletmek için** (test Gmail hesabı `.env`'e yazıldıktan sonra), `backend` klasöründe:

```powershell
uv run flowpilot worker
```
```powershell
uv run flowpilot latency
```

İlki açık kaldığı sürece gelen e-postaları işler (Ctrl+C ile durur); ikincisi gelişten öneriye geçen süreleri gösterir.

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
| Kaynak kontrolü | Ajanın okuduğu her sayının belgede gerçekten yazıp yazmadığının kontrolü. Yazmıyorsa "şüpheli". |
| Satın alma taslağı | Aynı talebe gelen teklifler arasından ürün başına seçilen tedarikçi listesi. Onaylanınca kaydedilir, kimseye gönderilmez. |
| Yanıt taslağı | Ajanın hazırladığı cevap metni. Onaylansa bile gönderilmez; yalnızca kaydedilir. |
| Demo kur | Karşılaştırma için kullanılan sabit kur (1 EUR = 37,50 TL, 1 USD = 34,80 TL). Gerçek kur değildir. |
| Ajan | Departmanın işini hazırlayan yapay zekâ (ilki M5'te). Sadece **önerir**, onay insanındır. |
| Öneri | Ajanın hazırladığı iş (ör. "bu teklifi kaydet"). Onaylanınca bir kez uygulanır, reddedilirse hiç. |
| Denetim kaydı | Sistemde olan her şeyin silinemeyen listesi: kim, ne zaman, ne yaptı. |
| İşleyici (worker) | Arka planda sürekli çalışan parça: posta kutusunu izler, gelen e-postayı baştan sona işler. |
| IMAP / IDLE | IMAP: posta kutusunu okumanın standart yolu. IDLE: "yeni e-posta gelince bana haber ver" özelliği; böylece sistem sürekli sormak zorunda kalmaz. |
| Uygulama şifresi | Google'ın, bir programın posta kutusunu okuması için verdiği ayrı şifre. Hesap şifren değildir, istediğinde iptal edilir. |
| Seed | Demo için hazırladığımız kurgusal şirket verisi (Atlas Endüstri). |
| Değerlendirme seti | Doğru cevabını bildiğimiz örnek e-postalar; sistemin ne kadar doğru çalıştığını ölçmek için. |
| ADR | "Neden böyle yaptık" kaydı. `docs/KARARLAR.md`'de durur. |
| CI | GitHub'da her yüklemede testleri otomatik çalıştıran sistem. Yeşil = her şey yolunda. |
