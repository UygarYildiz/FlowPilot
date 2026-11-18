# Mimari

> Bu belge **bugün var olan** sistemi anlatır. Henüz yazılmamış parçalar yalnızca "Planlanan" bölümünde durur
> ve kod yazıldıkça yukarı taşınır. Bir bileşen değiştiğinde bu belge aynı commit'te güncellenir.

**Son güncelleme:** 2026-11-18 (M0 iskelet)

## Var olan
Yığın: ADR-009. Şu an yalnızca iskelet (M0) var.

| Bileşen | Yer | Ne yapar |
|---|---|---|
| API | `backend/src/flowpilot/main.py` | FastAPI uygulaması; şimdilik yalnızca `/health`. |
| Ayarlar | `backend/src/flowpilot/config.py` | `FLOWPILOT_` önekli ortam değişkenleri. |
| Model arayüzü | `backend/src/flowpilot/llm/` | `LLMClient` protokolü (şemalı çıktı) ve testler için `FakeLLM` (ADR-008). Gemini uygulaması M2'de. |
| Çekirdek | `backend/src/flowpilot/core/` | Boş; M1'den itibaren dolacak. |
| Departmanlar | `backend/src/flowpilot/departments/` | Boş; M2'de kayıt defteriyle. |
| Panel | `frontend/` | React + Vite iskeleti; geliştirmede `/api` isteklerini FastAPI'ye yönlendirir. |
| CI | `.github/workflows/ci.yml` | ruff, pyright, import-linter, pytest; oxlint, build, vitest. |

## Bileşenler ve sınırlar
<!-- Kod yazıldıkça her bileşen için: ne yapar, nerede durur (klasör), kime bağımlı, kim ona bağımlı. -->

## Veri akışı
<!-- Bir e-postanın girişten onaya kadar izlediği yol. Kod yazılınca diyagram eklenecek. -->

## Bağımlılık kuralları
Kurallar `backend/pyproject.toml` içindeki import-linter sözleşmeleriyle korunur (`uv run lint-imports`, CI'da da).
Şu an etkin: kural 1 ve "llm katmanı core ve departmanlardan bağımsız". Kural 2 (departmanlar birbirinden bağımsız)
ilk departman paketiyle birlikte (M2) sözleşmeye eklenecek.

1. Decision Engine hiçbir departman modülünü import etmez; departmanları yalnızca sözleşme üzerinden tanır.
2. Departman modülleri birbirini import etmez.
3. Departman ajanları veriyi doğrudan değiştirmez; yalnızca öneri kaydeder. Değişikliği onaydan sonra çekirdekteki tek yürütücü uygular.
4. Yeni departman eklemek çekirdek kodda değişiklik gerektirmez. Gerektiriyorsa önce sözleşme düzeltilir (ADR ile).

## Planlanan
- **Giriş katmanı:** e-postaları ve eklerini alır, kaydeder, tekrarları ayıklar.
- **Decision Engine:** yapılandırılmış karar üretir (departman, kategori, intent, öncelik, güven skoru, önerilen işlem, onay gereksinimi). Güven düşükse manuel incelemeye gönderir.
- **Departman modülleri:** her biri kendi kategorilerini, ajanını, araçlarını ve yetkilerini sözleşmeyle tanımlar.
- **Onay ve yürütme:** önerileri insana gösterir; onaylananları tek bir yürütücü bir kez uygular; her adım denetim kaydına yazılır.
- **Panel:** merkezi inbox, departman inbox'ları, karar gerekçesi, onay/ret, düzeltme, geçmiş.
