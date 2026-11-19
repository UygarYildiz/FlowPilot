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

## ADR-014: Ajan sözleşmesi, öneri yaşam döngüsü ve tek yürütücü
**Tarih:** 2026-11-19 · **Durum:** Kabul edildi
**Bağlam:** M4 (v1 kapsamı 3.3–3.4, başarı kriteri 7): departman ajanları öneri üretir, insan onaylar, onaylanan tam bir kez uygulanır; reddedilen hiç uygulanmaz. Ajanlar veriyi doğrudan değiştirmez (MIMARI.md kural 3).
**Karar:**
- Sözleşme (`core/registry.py`): `Department.agent` (`handle(AgentContext) → [ProposalDraft]`) ve `Department.proposal_types` (`ProposalType`: anahtar, etiket, pydantic veri şeması, `requires_approval`, `apply(ApplyContext, payload)`). Ajanlı departmanın en az bir öneri tipi olmalı. `AgentContext` salt veridir (e-posta, ek metinleri, kendi rotası); veritabanı oturumu içermez. Araçlar (`tools`) M5'te eklenir.
- Çekirdek tablolar: `AgentRun` (rota başına bir tane, tekil `route_id`; `running → succeeded | failed`, başarısız olan yeniden çalıştırılabilir) ve `Proposal` (`pending → approved → executed`, `pending → rejected`, uygulama hatasında `failed`, yeniden denenebilir).
- Ajan çıktısı tamamen doğrulanır (bilinmeyen tip ya da şemaya uymayan veri → çalıştırma `failed`, hiçbir öneri kaydedilmez). `idempotency_key` = rota + tip + kanonik veri özetidir ve tekildir: aynı öneri iki kez kaydedilmez.
- **Tek yürütücü** `core/proposals.execute`: satırı `SELECT … FOR UPDATE` ile kilitler; yalnızca `approved` ya da `failed` öneriyi uygular, `executed` ise hiçbir şey yapmaz. `apply` bir SAVEPOINT içinde, durum değişikliğiyle aynı işlemde çalışır: ya ikisi birden kalıcı olur ya hiçbiri. `apply`'a `idempotency_key` verilir (dış sistem yazımları için; v1'de yalnızca FlowPilot'un kendi tabloları).
- Ret gerekçe ister. `requires_approval=False` tipler oluşturulunca sistem adına onaylanıp hemen uygulanır.
- E-posta durumu: bekleyen öneri varsa `awaiting_approval`, kalmayınca `routed`. Rotanın kapanması (işlendi) kullanıcıdadır.
- Denetim kaydı: `agent.ran`, `agent.failed`, `proposal.created/approved/rejected/executed/failed` e-postanın olayları olarak yazılır (`data.proposal_id`). Panelde yöneticiye tüm sistemin denetim kaydı ekranı.
**Sonuçlar:** Kriter 7 kilit + durum kontrolü + aynı işlem ile kanıtlanır. Bedeli: `apply` yalnızca veritabanına yazdığı sürece "tam bir kez" garantilidir; dış sisteme yazan bir `apply` (v1 dışı) `idempotency_key`'i karşı tarafta kullanmalıdır.

## ADR-015: Procurement Agent — teklif çıkarma, sayı doğrulama, araçlar ve karşılaştırma
**Tarih:** 2026-11-20 · **Durum:** Kabul edildi
**Bağlam:** M5 (v1 kapsamı 3.6–3.7, kriter 4–5): teklif belgesinden alan çıkarma, uydurulmuş sayı olmaması, aynı talebe gelen tekliflerin karşılaştırılması. Ajan veritabanına yazamaz (ADR-014) ama karşılaştırma için kayıtlı teklifleri okuması gerekir.
**Karar:**
- **Araçlar (sözleşmeye ek):** `Department.tools` = `Tool(name, description, fn(session, **kwargs))`. Çekirdek ajana `AgentContext.tools` (bir `ToolBox`) verir; her çağrı bir SAVEPOINT içinde çalışır ve sonunda geri alınır: araç yazsa bile kalıcı olmaz. Araçlar düz veri döndürür (ORM nesnesi değil).
- **Çıkarma:** generatif model (Gemini, `LLMClient`) şemalı çıktı üretir: tedarikçi, teklif no, talep no, para birimi, geçerlilik, satırlar (kod, ürün, miktar, birim, birim fiyat, satır tutarı, teslim süresi), ara toplam, KDV, genel toplam. Belgede yazmayan alan boş bırakılır; model hesap yapmaz. Ajanın modeli bileşim kökünde tembel kurulur (`llm_factory`).
- **Doğrulama (deterministik, modelden bağımsız):** (1) **kaynak kontrolü:** her sayı belge metninde geçmeli (TR `1.234,56` ve EN `1,234.56` biçimleri); geçmeyen "kaynakta yok" diye işaretlenir; (2) miktar > 0; (3) miktar × birim fiyat = satır tutarı, satırlar = ara toplam, ara toplam + KDV = genel toplam (0,01 tolerans); (4) para birimi belli mi; (5) ürün kodu demo kataloğunda mı (uyarı). Hiçbir değer düzeltilmez ya da uydurulmaz; işaretlenir ve panelde gösterilir. Kriter 5 "işaretsiz geçip yanlış çıkan tutar" olarak ölçülür.
- **Tablolar** Satın Alma paketinin kendisindedir (`procurement_supplier`, `procurement_quote`, `procurement_quote_line`, `procurement_purchase_draft`); çekirdek bilmez. Göç ortamı departman modellerini ayrıca içe aktarır.
- **Öneri tipleri (1. parça):** `record_quote` (teklifi kaydet) ve `purchase_draft` (aynı talepte en az iki tedarikçi varsa: ürün başına en düşük birim fiyat, sabit demo kuruyla TRY'ye çevrilerek; teslim süresi ve geçerlilik gerekçede). Seçim kullanıcınındır. Diğer intent'ler (`price_update`, yanıt taslakları, `purchase_request`) 2. parçada.
- **Ölçüm:** `evals/extraction/` altında betikle üretilen ≥30 teklif belgesi (PDF/XLSX/CSV, farklı düzenler, bilinçli tuzaklar) ve beklenen alanlar; `flowpilot eval extraction`.
**Sonuçlar:** Sayıların doğruluğu modele değil kaynak metne ve aritmetiğe dayanır. Bedeli: taranmış görüntü (OCR yok) ve kaynakta farklı yazılmış sayılar (ör. "1,62" yerine "1.62") için kaynak kontrolü ikinci biçimi de tanır; tanımadığı biçim yanlış "kaynakta yok" uyarısı üretebilir (güvenli taraf).
