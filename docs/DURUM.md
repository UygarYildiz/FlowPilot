# Durum — nerede kaldık?

> Her çalışma oturumunun sonunda güncellenir. Bu dosya **kısa** kalır (en fazla ~60 satır).
> Geçmiş burada birikmez: biten işler `gunluk/` ve `CHANGELOG.md`'ye gider.

**Son güncelleme:** 2026-11-19
**Aktif sürüm:** v1 — Çekirdek + Procurement ([kapsam](surumler/v1.md))
**Aşama:** M0–M3 bitti (yönlendirme seti 150, hedefler tuttu). M4 (onay) başlamadı.
**Yığın:** ADR-009 — Python/FastAPI, PostgreSQL, React/Vite. Sınıflandırma: ADR-013 kademeli — SubQ `subq-snap-1.2` → Gemini `gemini-3.5-flash-lite` → insan.
**Uzak depo:** https://github.com/UygarYildiz/FlowPilot (`main`, CI: GitHub Actions)

## Son ölçüm (kademeli motor, test yarısı 74 e-posta, canlı, 2026-11-19)
Departman %97,3 (hedef ≥90) · otomatik yönlendirilenlerde hata %1,5 (≤5; 1 e-posta) · Procurement intent %100 (≥85)
· tüm intent %97,3 · çok departmanlı geri çağırma %100 · manuel inceleme %10,8. SubQ 58 e-postada karar verdi
(52 otomatik), Gemini 16'da (14 otomatik): Gemini çağrısı tek başına Gemini'ye göre ~%78 az.
Rapor: `backend/evals/results/routing-20261119-150223-cascade-*.md`. Tek otomatik hata ev-107: SubQ doğru ama
emin değildi (Satış %59); Gemini bu sefer Lojistik'i %85 ile ekledi (önceki çalıştırmada %60 → inceleme).
Gemini'nin güveni çalıştırmadan çalıştırmaya değişiyor.

## Motor karşılaştırması (özet; ayrıntı `gunluk/2026-11.md` 6–12, ADR-013)
Test yarısı: Gemini %97,3 / otomatik hata %0 / inceleme %12,2 · SubQ %95,9 / %0 / %29,7 · Clef-flash %71,6 · Clef %77,0.
150 e-posta: Gemini 4 yanlış otomatik, SubQ 0. SubQ kalibre (p 0,50–0,75 → %53 doğru); Gemini neredeyse hep ≥0,9 der.
Denenip bırakılanlar: "belirsiz" eşiğini gevşetmek, `typed-v3` (asıl + ek departman soruları).

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
- `backend/.env`: `FLOWPILOT_DECISION_ENGINE=cascade`, `FLOWPILOT_LLM_PROVIDER=gemini` (önceden `fake`); `SUBQ_API_KEY` dolu.
  Kademeli kararla paneldeki fiş tarayıcıda görülmedi (geliştirme DB'sinde bekleyen e-posta yoktu).

## Engeller
- Yok.
