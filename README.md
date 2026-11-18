# FlowPilot

Şirketlere gelen e-postaları yapay zekâyla sınıflandırıp ilgili departmana yönlendiren, departman ajanlarıyla işlem öneren ve kritik işlemlerde insan onayını koruyan bir AI operasyon platformu.

Proje geliştirme aşamasında. Nerede olduğumuzu görmek için: [docs/DURUM.md](docs/DURUM.md)

## Belgeler
| Belge | İçerik |
|---|---|
| [docs/VIZYON.md](docs/VIZYON.md) | Ürün fikri ve uzun vadeli vizyon |
| [docs/DURUM.md](docs/DURUM.md) | Nerede kaldık, sıradaki adım, açık sorular |
| [docs/YOL_HARITASI.md](docs/YOL_HARITASI.md) | Sürümler ve departman sırası |
| [docs/MIMARI.md](docs/MIMARI.md) | Bugünkü mimari ve bağımlılık kuralları |
| [docs/KARARLAR.md](docs/KARARLAR.md) | Mimari karar kayıtları (ADR) |
| [docs/gunluk/](docs/gunluk/) | Oturum oturum çalışma günlüğü |
| [docs/departmanlar/](docs/departmanlar/) | Departman başına kapsam ve ajan tanımı |
| [CHANGELOG.md](CHANGELOG.md) | Yayına alınan sürümler |

## Geliştirme kurulumu
Depoyu klonladıktan sonra belge kontrolü yapan git hook'unu etkinleştirin:

```
git clone https://github.com/UygarYildiz/FlowPilot.git
cd FlowPilot
git config core.hooksPath .githooks
```

Gereken araçlar: [uv](https://docs.astral.sh/uv/), Node.js 24, Docker.

```
docker compose up -d                                  # PostgreSQL (localhost:5433)
cd backend && uv sync
uv run alembic upgrade head                           # şemayı kur
uv run flowpilot ingest seed                          # kurgusal Atlas Endüstri e-postaları
uv run uvicorn flowpilot.main:app --reload
cd frontend && npm install && npm run dev             # http://localhost:5173
```

Kontroller (CI'da da aynıları çalışır):

```
cd backend && uv run ruff check . && uv run pyright && uv run lint-imports && uv run pytest
cd frontend && npm run lint && npm run build && npm test
```
