# Mimari

> Bu belge **bugün var olan** sistemi anlatır. Henüz yazılmamış parçalar yalnızca "Planlanan" bölümünde durur
> ve kod yazıldıkça yukarı taşınır. Bir bileşen değiştiğinde bu belge aynı commit'te güncellenir.

**Son güncelleme:** 2026-11-19 (M3 panel)

## Var olan
Yığın: ADR-009. M0 (iskelet), M1 (e-posta girişi), M2 (karar) ve M3 (panel) var.

| Bileşen | Yer | Ne yapar |
|---|---|---|
| API | `main.py`, `api/` | FastAPI. `api/routes.py`: `/api/auth/*` (giriş/çıkış/me), `/api/counts`, `/api/emails` (liste: tümü / inceleme / departman, arama), `/api/emails/{id}` (ayrıntı + geçmiş), ek indirme, `correction`, `dismiss`, `/api/routes/{id}/done`. İmzalı oturum çerezi (`SessionMiddleware`, ADR-012). Yalnızca HTTP katmanı; iş kuralları `core/workflow.py`'de. |
| Kullanıcılar | `core/users.py` | argon2 şifre özeti, `authenticate`, demo hesapları (`flowpilot users demo`). Roller: `admin` her şeyi görür; `department_user` yalnızca kendi departmanına yönlenmiş ve incelemede olmayan e-postaları. |
| Panel işlemleri | `core/workflow.py` | `correct_routes` (yeni manuel karar + `Correction` + denetim), `mark_route_done` (tüm rotalar kapanınca e-posta `done`), `dismiss` (ilgisiz e-postayı kapat). |
| Ayarlar | `backend/src/flowpilot/config.py` | `FLOWPILOT_` önekli ortam değişkenleri. |
| Model arayüzü | `backend/src/flowpilot/llm/` | `LLMClient` protokolü (şemalı çıktı); `FakeLLM` (testler, ADR-008); `GeminiClient` (`google-genai`, JSON şeması, 429/5xx/ağ hatasında bekleyip yeniden dener). `factory.build_llm` ayara göre seçer. `decision_model.py`: karar modelleri (System One API) için `ClefClient` (Workers AI REST), `SubQClient` (SubQ Decisions API, `POST /v1/systemone`, `subq-snap-1.2`) ve `FakeDecisionModel`; yeniden deneme ortak `_post`'ta. İki hata türü: `LLMError` = geçersiz çıktı/kalıcı hata; `LLMUnavailableError` = geçici erişilemezlik. |
| Veritabanı | `core/db.py`, `core/models.py`, `backend/migrations/` | SQLAlchemy 2 modelleri: `Email`, `Attachment`, `Decision`, `Route` (durum: open/done), `Correction`, `User` (`app_user`), `AuditEvent`. `Email.current_decision_id` geçerli kararı gösterir. Şema Alembic göçleriyle kurulur. |
| Denetim kaydı | `core/audit.py` | `record()` ile olay ekler; çağıranın işlemiyle birlikte commit olur. Kayıtlar güncellenmez. |
| Ek depolama | `core/storage.py` | `AttachmentStorage` arayüzü; `LocalStorage` (disk), `MemoryStorage` (test). İçerik adresli anahtar: `sha256/ab/abcd…`. |
| Giriş adaptörleri | `core/ingestion/sources/` | `SeedSource` (`backend/seed/atlas/emails.json` + ekler) ve `ImapSource` (salt-okunur, `BODY.PEEK[]`, son N gün). Ortak arayüz: `EmailSource.fetch()`. |
| Ek metni çıkarma | `core/ingestion/extract.py` | PDF (pdfplumber), XLSX (openpyxl), CSV, düz metin → metin; diğerleri `unsupported`, bozuk dosya `failed`. |
| Giriş servisi | `core/ingestion/service.py`, `runner.py` | E-postayı ekleriyle tek işlemde kaydeder, tekrarı ayıklar, denetim kaydına yazar. Her e-posta ayrı işlemde. |
| Departman sözleşmesi | `core/registry.py` | `Department` (key, name, description, intents) ve `DepartmentRegistry`. Ajan/araç/öneri alanları M4–M5'te eklenecek. |
| Departmanlar | `departments/<ad>/__init__.py` | `procurement`, `finance`, `sales_orders`, `logistics`: her biri bir `DEPARTMENT` tanımı. Henüz ajan yok. |
| Bileşim kökü | `bootstrap.py` | Departmanları kayıt defterine bağlar (ADR-010). Yeni departman = yeni paket + burada bir satır. |
| Decision Engine | `core/decision/` | `engine.py`: `Classifier` protokolü; `LLMClassifier` (generatif, `decision-v1` prompt, şema + doğrulama + bir yeniden deneme) ve `decide` (sonucu kaydeder). `typed.py`: `DecisionModelClassifier` (karar modeli, `typed-v1`: departman başına evet/hayır, departman başına intent seçimi, öncelik puanı). `runner.py`: `received` e-postaları işler. Motor `decision_setup.py`'de ayardan seçilir (`FLOWPILOT_DECISION_ENGINE=llm|clef|subq`). |
| Değerlendirme | `evals/routing.py`, `backend/evals/` | Etiketli set (`evals/routing/dataset.jsonl`), ölçüm ve rapor (`evals/results/`). |
| CLI | `cli.py` | `flowpilot ingest seed|imap`, `flowpilot classify`, `flowpilot eval routing`. |
| Panel | `frontend/src/` | React + Vite + Tailwind 4 + React Router + TanStack Query. Sayfalar: giriş, gelen kutuları (tümü / "İnsan baksın" / departman), e-posta ayrıntısı (yönlendirme fişi, düzeltme, ekler, geçmiş). Ekran metinleri `lib/text.ts`'de (dil değişirse tek dosya). Geliştirmede `/api` → `127.0.0.1:8000`. |
| CI | `.github/workflows/ci.yml` | ruff, pyright, import-linter, pytest (PostgreSQL servisiyle); oxlint, build, vitest. |

Tablodaki `core/`, `api/`, `departments/`, `evals/`, `main.py`, `bootstrap.py`, `cli.py` yolları `backend/src/flowpilot/` altındadır.

## Bileşenler ve sınırlar
<!-- Kod yazıldıkça her bileşen için: ne yapar, nerede durur (klasör), kime bağımlı, kim ona bağımlı. -->

## Veri akışı
Bugün var olan kısım (girişten kayda):

```
EmailSource.fetch()  ──►  IncomingEmail  ──►  ingest()  ──►  Email(status=received) + Attachment[] + AuditEvent
 (seed | imap)            (bellekte)          │
                                              ├─ tekrar mı? Message-ID veya içerik özeti eşleşirse → mevcut kayıt,
                                              │  AuditEvent "email.duplicate_ignored"
                                              ├─ ekler → depoya (içerik adresli) + metin çıkarma
                                              └─ eşzamanlı kopya → message_id tekil kısıtı yakalar
```

- **İçerik özeti:** gönderen + konu + boşlukları sadeleştirilmiş gövde + eklerin sha256'ları. Tarih dahil değil.
- **Message-ID yoksa:** `<içerik-özeti@flowpilot.invalid>` üretilir.

Sınıflandırma (`flowpilot classify`):

```
Email(received) ──► classify(): prompt (kayıt defteri + e-posta + ek kesitleri) ──► LLM (şemalı JSON)
                     │ doğrula: departman/intent kayıt defterinde mi? değilse veya LLMError → bir kez daha dene
                     │ iki deneme de olmazsa → rota yok, needs_review
                     │ aynı departman iki kez → güveni yüksek olan; 'unknown' başka rotanın yanında atılır
                     ▼
               decide(): Decision + Route[] kaydı, AuditEvent "email.classified"
                     ├─ unknown veya güven < eşik (0.75) → Email(needs_review)
                     └─ aksi halde → Email(routed)
LLMUnavailableError (kota/ağ/sunucu, denemeler tükendi) → işlem geri alınır, e-posta received kalır, döngü durur.
```

Panelden (insan):

```
needs_review ──► Departmana yönlendir (correct_routes: yeni manuel Decision, Correction) ──► routed
             └─► İlgisiz olarak kapat (dismiss, yalnızca admin) ──────────────────────────► done
routed ──► her departman kendi rotasını "İşlendi olarak kapat" (mark_route_done) ──► hepsi kapanınca done
```

- Sonrası (ajan, onay) "Planlanan"da.

## Bağımlılık kuralları
Kurallar `backend/pyproject.toml` içindeki import-linter sözleşmeleriyle korunur (`uv run lint-imports`, CI'da da).
Etkin sözleşmeler: kural 1, kural 2 (yeni departman listeye eklenmeli), "llm katmanı core ve departmanlardan
bağımsız", "departmanlar bootstrap, CLI ve API'yi import etmez", "core API/CLI/bootstrap/main'i import etmez".

1. Decision Engine hiçbir departman modülünü import etmez; departmanları yalnızca sözleşme üzerinden tanır.
2. Departman modülleri birbirini import etmez.
3. Departman ajanları veriyi doğrudan değiştirmez; yalnızca öneri kaydeder. Değişikliği onaydan sonra çekirdekteki tek yürütücü uygular.
4. Yeni departman eklemek çekirdek kodda değişiklik gerektirmez. Gerektiriyorsa önce sözleşme düzeltilir (ADR ile).

## Planlanan
- **Giriş:** canlıda S3 uyumlu depolama (R2); seed e-postalarının zamanlanmış gönderimi (M6).
- **Departman sözleşmesinin geri kalanı:** ajan, araçlar, öneri tipleri ve görünümler (M4–M5).
- **Onay ve yürütme:** önerileri insana gösterir; onaylananları tek bir yürütücü bir kez uygular; her adım denetim kaydına yazılır.
- **Onay/ret ekranı ve denetim kaydı ekranı** (M4); demo verisini sıfırlama ve paneli FastAPI'den sunma (M6).
