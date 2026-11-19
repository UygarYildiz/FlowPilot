# Kararlar (ADR)

> Mimari ve kapsamı etkileyen her karar buraya yeni bir kayıt olarak eklenir. Kayıtlar silinmez ve yeniden yazılmaz:
> bir karar değişirse yeni bir ADR yazılır, eskisinin durumu "Yerini ADR-00X aldı" olur.

Şablon:
```
## ADR-00X: Başlık
**Tarih:** YYYY-AA-GG · **Durum:** Kabul edildi | Yerini ADR-00Y aldı
**Bağlam:** Neden bir karar gerekti?
**Karar:** Ne seçtik?
**Sonuçlar:** Neyi kazanıyoruz, neyden vazgeçiyoruz?
```

---

## ADR-001: Departman departman artırımlı geliştirme
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Proje dört departman ve tam bir panel içeriyor; hepsini birden yapmak uzun sürer ve yarım kalma riski yüksek.
**Karar:** Her sürüm bir departmanı canlıya alır. Sıra: v1 Çekirdek + Procurement, v2 Finance, v3 Sales & Orders, v4 Logistics. Uygulama yayındayken bir sonraki departman eklenir.
**Sonuçlar:** Her sürüm kendi başına çalışan, gösterilebilir bir ürün olur. Buna karşılık çekirdek ilk sürümde sağlam kurulmalı, sonradan departman başına yeniden yazılmamalı.

## ADR-002: İlk sürüm çekirdeği tam kurar
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Çekirdeği departman departman büyütmek her sürümde temelin yeniden yazılmasına yol açar.
**Karar:** v1; e-posta girişi, Decision Engine, merkezi inbox, onay akışı ve denetim kaydını içerir. Sonraki sürümler yalnızca departman modülü ekler.
**Sonuçlar:** v1 daha uzun sürer; sonraki sürümler hızlanır.

## ADR-003: Decision Engine ilk günden tüm departmanları tanır
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Yalnızca Procurement yayında olsa da gerçek bir inbox'a fatura ve sevkiyat e-postaları da gelir.
**Karar:** Decision Engine dört departmanı da sınıflandırır. Ajanı olmayan departmanın e-postası o departmanın inbox'ına düşer ve manuel işlenir.
**Sonuçlar:** Her yeni departman, var olan bir inbox'a ajan eklemek anlamına gelir. Sınıflandırma doğruluğu v1'den itibaren dört departman için ölçülür.

## ADR-004: Departman sözleşmesi v1'de tanımlanır
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Genişletilebilirlik ancak yeni departmanın çekirdeğe dokunmadan eklenebilmesiyle kanıtlanır.
**Karar:** Bir departmanın sağladıkları (kategoriler/intent'ler, ajan, araçlar, yetkiler, onay kuralları) v1'de bir sözleşmeyle tanımlanır. v2 bu sözleşmenin sınavıdır; çekirdeğe dokunmak gerekirse sözleşme yeni bir ADR ile düzeltilir.
**Sonuçlar:** v1'de ek tasarım işi; sonraki departmanlarda öngörülebilir ekleme.

## ADR-005: Her sürümde regresyon ölçümü
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Yeni departman eklemek eski departmanların yönlendirme doğruluğunu bozabilir.
**Karar:** Kurgusal e-postalardan oluşan bir değerlendirme seti tutulur ve her departmanla büyür. Bir sürüm, önceki departmanların doğruluğu düşmeden yayına alınır. Sonuçlar CHANGELOG'a yazılır.
**Sonuçlar:** Her sürümde değerlendirme seti hazırlama işi; karşılığında ölçülebilir kalite.

## ADR-006: Proje belgeleri ve güncellik kuralları
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Proje büyüdükçe nerede kalındığı, neden öyle yapıldığı ve sistemin nasıl çalıştığı kaybolmamalı.
**Karar:** Durum, yol haritası, mimari, kararlar, günlük ve changelog ayrı dosyalarda tutulur (kurallar CLAUDE.md'de). Kod değiştiğinde DURUM.md'nin güncellenmesi iki kontrolle zorlanır: Claude Code Stop hook'u ve git pre-commit hook'u.
**Sonuçlar:** Her oturumun sonunda birkaç dakikalık belge güncellemesi; karşılığında her oturum kaldığı yerden başlar.

## ADR-007: E-posta girişi adaptör arkasında; v1'de seed + IMAP
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** Demo herkese açık olacak ve tekrarlanabilir olmalı; ama sistemin gerçek e-postayla da çalıştığı gösterilmeli. Gmail API OAuth onayı ve sağlayıcıya bağımlılık getirir.
**Karar:** Giriş bir adaptör arayüzü arkasında durur. v1'de iki adaptör: kurgusal e-postaları gönderen seed/simülasyon adaptörü (demo) ve IMAP adaptörü. Gmail API / Microsoft 365 sonraki sürümlere kalır.
**Sonuçlar:** Demo dış hesaba bağlı değil ve sıfırlanabilir. Yeni kaynak eklemek yeni adaptör yazmaktır; çekirdek değişmez.

## ADR-008: LLM bir arayüz arkasında; testlerde deterministik sahte model
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** CI'da her push'ta gerçek LLM çağırmak pahalı ve sonuçları değişken; sağlayıcı da sonradan değişebilir.
**Karar:** Decision Engine ve ajanlar modele yalnızca bir arayüz üzerinden ulaşır. Testler ve CI, kayıtlı cevaplar döndüren deterministik sahte modelle çalışır. Gerçek modelle değerlendirme her sürüm öncesi elle çalıştırılır. Sağlayıcı seçimi yığın ADR'sinde yapılır.
**Sonuçlar:** CI hızlı ve ücretsiz; sağlayıcı değiştirmek tek modülü etkiler. Buna karşılık sahte modelin kayıtlı cevapları bakım ister.

## ADR-009: Teknoloji yığını
**Tarih:** 2026-11-18 · **Durum:** Kabul edildi
**Bağlam:** v1'e başlamak için backend, veritabanı, kuyruk, frontend, LLM ve barındırma seçilmeli. Ölçütler: AI/otomasyon ilanlarıyla uyum, az hareketli parça, belge işleme gücü, düşük maliyet.
**Karar:**
- **Backend:** Python 3.12, FastAPI, Pydantic (v2), pydantic-settings. Paketler `uv` ile yönetilir.
- **Veritabanı:** PostgreSQL; SQLAlchemy 2 + Alembic.
- **İş kuyruğu:** PostgreSQL üzerinde (`SKIP LOCKED`, ör. procrastinate). Ayrı Redis yok.
- **Frontend:** React + TypeScript + Vite; TanStack Query; Tailwind. Paketler `npm` ile.
- **LLM:** Google Gemini API (`google-genai` SDK), ücretsiz katman. Model adı ortam değişkeninden okunur; somut model M2'de değerlendirme setiyle seçilir. ADR-008'deki arayüzün arkasındadır.
- **Ajan yapısı:** Agent çatısı yok; akış kendi kodumuzda, LLM yapılandırılmış çıktı (JSON şeması) ile çağrılır.
- **Belge okuma:** pdfplumber (PDF), openpyxl/pandas (XLSX, CSV).
- **Ek depolama:** geliştirmede yerel disk, canlıda S3 uyumlu depolama (Cloudflare R2); arayüz arkasında.
- **Kalite:** pytest, import-linter (MIMARI.md bağımlılık kuralları), ruff, pyright; frontend'de vitest.
- **Yerel geliştirme:** Docker Compose (PostgreSQL). **CI:** GitHub Actions. **Barındırma:** Render (web servisi + worker + PostgreSQL), `render.yaml` ile.
**Sonuçlar:**
- Gemini ücretsiz katmanı geliştirme ve denemeyi bedava yapar. Bedeli: istek/dakika ve günlük sınırlar (değerlendirme setleri yavaş çalıştırılır, canlı demoda yeni işlem sınırlanır) ve ücretsiz katmanda gönderilen içeriğin Google tarafından ürün geliştirmede kullanılabilmesi. Bu yüzden ücretsiz katmana yalnızca kurgusal veri gönderilir; IMAP ile gerçek posta kutusu bağlanırsa ücretli katman gerekir.
- Sağlayıcı değişirse yalnızca `llm/` altındaki uygulama değişir.
- Redis olmadığı için tek veritabanı yedeklenir; kuyruk yükü büyürse yeni ADR ile ayrı kuyruğa geçilir.

## ADR-010: Departmanlar bir bileşim kökünde kayıt defterine bağlanır
**Tarih:** 2026-11-19 · **Durum:** Kabul edildi
**Bağlam:** Decision Engine departmanların intent listesine ihtiyaç duyar, ama çekirdek departman paketlerini import edemez (MIMARI.md kural 1). Departmanlar bir yerde kayıt defterine eklenmeli.
**Karar:** Sözleşme (`Department`, `Intent`, `DepartmentRegistry`) çekirdekte durur. Departman paketleri yalnızca bu sözleşmeyi import eder ve bir `DEPARTMENT` tanımı dışa verir. Çekirdeğin dışındaki `flowpilot/bootstrap.py` departmanları açık bir listeyle kayıt defterine ekler; CLI ve API kayıt defterini oradan alır. Otomatik keşif (paket tarama, entry point) kullanılmaz.
**Sonuçlar:** Yeni departman = yeni paket + `bootstrap.py`'de bir satır + import-linter kural 2 listesine bir satır; çekirdek değişmez. Açık liste, hangi departmanların etkin olduğunu tek bakışta gösterir. Bedeli: kaydı unutulan bir departman sessizce devre dışı kalır (kayıt defteri testi dört departmanı doğrular).

## ADR-011: Kullanıcı için sade ilerleme belgesi
**Tarih:** 2026-11-19 · **Durum:** Kabul edildi
**Bağlam:** Teknik belgeler (DURUM, MIMARI, günlük) güncel olsa da proje sahibi ilerlemeyi takip etmekte zorlanıyor ve projeden koptuğunu söyledi.
**Karar:** Kök dizinde `ILERLEME.md`: teknik olmayan dille sistemin bugün ne yaptığı (örnekle), yol haritasında nerede olunduğu, son en fazla 3 oturum, sıradaki adım, kullanıcıdan beklenen kararlar ve küçük bir sözlük. ADR-006'daki Stop ve pre-commit kontrolleri artık `docs/DURUM.md` ile birlikte bu dosyayı da ister. Oturum sonu mesajları da aynı sade dille yazılır (CLAUDE.md).
**Sonuçlar:** Her oturumda birkaç dakikalık ek yazım; karşılığında proje sahibi teknik belgeleri okumadan güncel kalır.

## ADR-012: Panel oturumu, geçerli karar ve panel dili
**Tarih:** 2026-11-19 · **Durum:** Kabul edildi
**Bağlam:** M3 paneli için giriş, yetki ve "e-postanın şu anki yönlendirmesi" tanımı gerekiyordu. Panel dili için kullanıcıdan karar gelmedi.
**Karar:**
- Giriş: argon2 şifre özeti + Starlette `SessionMiddleware` ile imzalı çerez (yalnızca kullanıcı kimliği; 12 saat, `SameSite=Lax`, canlıda `Secure`). Panel ve API aynı kökenden sunulduğu için CSRF belirteci şimdilik yok; ayrı kökene geçilirse eklenir.
- Kararlar silinmez. `Email.current_decision_id` geçerli kararı gösterir; düzeltme yeni bir manuel karar ekler ve `Correction` kaydı açar (değerlendirme setine aday). Her rotanın kendi durumu (`open`/`done`) vardır.
- Panel dili Türkçe; tüm sabit metinler `frontend/src/lib/text.ts` ve sayfa bileşenlerinde, departman/intent adları API'den gelir. İngilizce gerekirse çeviri bu noktalardan yapılır.
**Sonuçlar:** Basit ve test edilebilir oturum; düzeltme geçmişi kaybolmaz. Bedeli: liste sorguları `current_decision_id` işaretçisinin güncel tutulmasına bağlı (`decide` ve `correct_routes` dışında karar ekleyen kod bunu da yapmalı).

## ADR-013: Kademeli sınıflandırma — önce karar modeli (SubQ), emin değilse Gemini
**Tarih:** 2026-11-19 · **Durum:** Kabul edildi
**Bağlam:** Karar modelleri (Cloudflare Clef, clef-flash, SubQ Snap 1.2) Gemini ile karşılaştırıldı (150 e-posta, dev/test bölmesi). İki Clef modeli elendi (test yarısında departman %72–77). SubQ, 150 e-postada Gemini kadar isabetli (%96,7 / %96,0), kalibre (p ≥ 0,9 → %100 doğru) ve hiç kendinden emin yanılmadı (Gemini 4). Ama tereddütünü dürüst bildirdiği için incelemeye iki kat fazla gönderiyor (%28 / %13). "Belirsiz" eşiğini gevşetmek ve `typed-v3` soru tasarımı bu farkı kapatmadı.
**Karar:** `FLOWPILOT_DECISION_ENGINE=cascade`: SubQ (`typed-v2`) önce bakar; emin değilse (incelemeye gidecekse) Gemini (`decision-v1`) bakar; o da emin değilse insan. SubQ "hiçbir departman değil" diyor ve güveni ≥ 0,95 ise Gemini çağrılmaz (ilgisiz e-posta her iki motorda da incelemeye gider). Kararın `model` alanı kararı veren son motoru yazar; gerekçe ve `raw_output` iki motorun da görüşünü taşır. Tek motorlu ayarlar (`llm`, `subq`, `clef`) kalır.
**Sonuçlar:** Kayıtlı ölçümler üzerindeki hesapta Gemini çağrıları ~%72 azalır, inceleme Gemini kadar (%13) kalır, yanlış otomatik yönlendirme 4 → 3. Erişilemezlik: SubQ yanıt vermezse Gemini karar verir; SubQ tereddüt edip Gemini yanıt vermezse SubQ önerisiyle insana gider; ikisi de yanıt vermezse e-posta sonra yeniden denenir. Bedeli: iki sağlayıcı ve iki eşik/soru setinin ayrı bakımı. Kesin sonuç gerçek ölçümle raporlanır (DURUM/günlük).
