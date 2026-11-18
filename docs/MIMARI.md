# Mimari

> Bu belge **bugün var olan** sistemi anlatır. Henüz yazılmamış parçalar yalnızca "Planlanan" bölümünde durur
> ve kod yazıldıkça yukarı taşınır. Bir bileşen değiştiğinde bu belge aynı commit'te güncellenir.

**Son güncelleme:** 2026-11-18 (M1 giriş)

## Var olan
Yığın: ADR-009. M0 (iskelet) ve M1 (e-posta girişi) var.

| Bileşen | Yer | Ne yapar |
|---|---|---|
| API | `backend/src/flowpilot/main.py` | FastAPI uygulaması; şimdilik yalnızca `/health`. |
| Ayarlar | `backend/src/flowpilot/config.py` | `FLOWPILOT_` önekli ortam değişkenleri. |
| Model arayüzü | `backend/src/flowpilot/llm/` | `LLMClient` protokolü (şemalı çıktı) ve testler için `FakeLLM` (ADR-008). Gemini uygulaması M2'de. |
| Veritabanı | `core/db.py`, `core/models.py`, `backend/migrations/` | SQLAlchemy 2 modelleri: `Email`, `Attachment`, `AuditEvent`. Şema Alembic göçleriyle kurulur. |
| Denetim kaydı | `core/audit.py` | `record()` ile olay ekler; çağıranın işlemiyle birlikte commit olur. Kayıtlar güncellenmez. |
| Ek depolama | `core/storage.py` | `AttachmentStorage` arayüzü; `LocalStorage` (disk), `MemoryStorage` (test). İçerik adresli anahtar: `sha256/ab/abcd…`. |
| Giriş adaptörleri | `core/ingestion/sources/` | `SeedSource` (`backend/seed/atlas/emails.json` + ekler) ve `ImapSource` (salt-okunur, `BODY.PEEK[]`, son N gün). Ortak arayüz: `EmailSource.fetch()`. |
| Ek metni çıkarma | `core/ingestion/extract.py` | PDF (pdfplumber), XLSX (openpyxl), CSV, düz metin → metin; diğerleri `unsupported`, bozuk dosya `failed`. |
| Giriş servisi | `core/ingestion/service.py`, `runner.py` | E-postayı ekleriyle tek işlemde kaydeder, tekrarı ayıklar, denetim kaydına yazar. Her e-posta ayrı işlemde. |
| CLI | `backend/src/flowpilot/cli.py` | `uv run flowpilot ingest seed` / `ingest imap`. |
| Departmanlar | `backend/src/flowpilot/departments/` | Boş; M2'de kayıt defteriyle. |
| Panel | `frontend/` | React + Vite iskeleti; geliştirmede `/api` isteklerini FastAPI'ye yönlendirir. |
| CI | `.github/workflows/ci.yml` | ruff, pyright, import-linter, pytest (PostgreSQL servisiyle); oxlint, build, vitest. |

Tablodaki `core/` yolları `backend/src/flowpilot/` altındadır.

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
- Sonrası (sınıflandırma, ajan, onay) "Planlanan"da.

## Bağımlılık kuralları
Kurallar `backend/pyproject.toml` içindeki import-linter sözleşmeleriyle korunur (`uv run lint-imports`, CI'da da).
Şu an etkin: kural 1 ve "llm katmanı core ve departmanlardan bağımsız". Kural 2 (departmanlar birbirinden bağımsız)
ilk departman paketiyle birlikte (M2) sözleşmeye eklenecek.

1. Decision Engine hiçbir departman modülünü import etmez; departmanları yalnızca sözleşme üzerinden tanır.
2. Departman modülleri birbirini import etmez.
3. Departman ajanları veriyi doğrudan değiştirmez; yalnızca öneri kaydeder. Değişikliği onaydan sonra çekirdekteki tek yürütücü uygular.
4. Yeni departman eklemek çekirdek kodda değişiklik gerektirmez. Gerektiriyorsa önce sözleşme düzeltilir (ADR ile).

## Planlanan
- **Giriş:** canlıda S3 uyumlu depolama (R2); seed e-postalarının zamanlanmış gönderimi (M6).
- **Decision Engine:** yapılandırılmış karar üretir (departman, kategori, intent, öncelik, güven skoru, önerilen işlem, onay gereksinimi). Güven düşükse manuel incelemeye gönderir.
- **Departman modülleri:** her biri kendi kategorilerini, ajanını, araçlarını ve yetkilerini sözleşmeyle tanımlar.
- **Onay ve yürütme:** önerileri insana gösterir; onaylananları tek bir yürütücü bir kez uygular; her adım denetim kaydına yazılır.
- **Panel:** merkezi inbox, departman inbox'ları, karar gerekçesi, onay/ret, düzeltme, geçmiş.
