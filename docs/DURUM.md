# Durum — nerede kaldık?

> Her çalışma oturumunun sonunda güncellenir. Bu dosya **kısa** kalır (en fazla ~60 satır).
> Geçmiş burada birikmez: biten işler `gunluk/` ve `CHANGELOG.md`'ye gider.

**Son güncelleme:** 2026-11-19
**Aktif sürüm:** v1 — Çekirdek + Procurement ([kapsam](surumler/v1.md))
**Aşama:** M0–M3 bitti (yönlendirme seti 150, hedefler tuttu). M4 (onay) başlamadı.
**Yığın:** ADR-009 — Python/FastAPI, PostgreSQL, React/Vite, LLM: Gemini `gemini-3.5-flash-lite` (ücretsiz katman).
**Uzak depo:** https://github.com/UygarYildiz/FlowPilot (`main`, CI: GitHub Actions)

## Son ölçüm (yönlendirme, 150 e-posta, `decision-v1`, 2026-11-19)
Departman %96,0 (hedef ≥90) · otomatik yönlendirilenlerde hata %3,1 (≤5) · Procurement intent %100 (≥85)
· tüm intent %98,6 · çok departmanlı geri çağırma %96,4 · manuel inceleme %12,7.
Rapor: `backend/evals/results/routing-20261119-100854-*.md`. 6 hatanın 4'ü fazladan departman ekleme.

## Şu an yapılan
- Yok. Sıradaki adımı bekliyor.

## Sıradaki adım
1. M4: departman sözleşmesine `agent` ve `proposal_types` (v1 kapsamı 3.3), `AgentRun` / `Proposal` modelleri,
   öneri yaşam döngüsü (pending → approved → executed / rejected / failed), tek yürütücü (idempotency),
   panelde onay/ret ve tüm sistem için denetim kaydı ekranı. Başarı kriteri 7 testle.
2. (İleride) Fazladan departman ekleme eğilimi için `decision-v2` prompt denemesi. Seti önce geliştirme/test diye
   ikiye ayır, prompt'u yalnızca geliştirme kısmına bakarak değiştir; test kısmı tarafsız kalsın.

## Açık sorular
- Panel dili Türkçe yapıldı (ADR-012); kullanıcı İngilizce isterse `frontend/src/lib/text.ts` + sayfalar çevrilir.
- Değerlendirme setine kullanıcının da (Claude dışında) birkaç gerçekçi e-posta eklemesi ölçümü daha güvenilir yapar.

## Notlar
- Panel yerelde: `.claude/launch.json` (api :8000, panel :5173). Demo hesaplar `uv run flowpilot users demo`, şifre `flowpilot-demo`.
- Tarayıcı denemeleri geliştirme veritabanını değiştirdi (1 e-posta kapatıldı, 1 düzeltildi, 1 rota kapatıldı). Sıfırlama komutu yok (M6).
- Kullanıcıya her oturum sonunda `ILERLEME.md` sade dille güncellenir (ADR-011); Stop/pre-commit kontrolü ister.
- Gemini ücretsiz katmanına yalnızca kurgusal veri gönderilir (ADR-009). `.env` gitignore'da.
- Docker Desktop kapanınca DB testleri atlanır (yerelde); `docker compose up -d` gerekir. DB `localhost:5433`.
- IMAP adaptörü yalnızca sahte sunucuyla test edildi.

## Engeller
- Yok.
