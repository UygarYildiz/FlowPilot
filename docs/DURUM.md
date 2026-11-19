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

## Karar modeli karşılaştırması (test yarısı, 74 e-posta, 2026-11-19) — kullanıcı kararı bekliyor
| | Gemini `decision-v1` | SubQ `subq-snap-1.2` `typed-v2` | Clef-flash `typed-v2` |
|---|---|---|---|
| Departman | %97,3 | %95,9 | %71,6 |
| Otomatik hata | %0,0 | %0,0 | %7,9 |
| Çok dep. geri çağırma | %100 | %100 | %71,4 |
| Manuel inceleme | %12,2 | %29,7 | %48,6 |
| Ortanca süre | — | 0,28 sn | 0,57 sn |
- SubQ dev yarısı: departman %97,4, otomatik hata %0, inceleme %26,3. Test yarısında incelemeye giden 22 e-postanın
  8'i ilgisiz (tasarım gereği); kalanların çoğu 0,5–0,75 arası "belki" departman kuralından.
- Raporlar: `evals/results/routing-20261119-13{1857,1938}-subq-*`, `...132028-cloudflare-clef-flash.*`.
- Öneri: Gemini kalsın, SubQ yedek motor (`--engine subq`); Clef elendi, büyük `clef` ölçülmedi.
  Kullanıcı onaylarsa ADR yazılır. SubQ incelemeyi azaltma (eşik/"belki" kuralı) yalnızca dev'e bakarak denenebilir.

## Sıradaki adım
0. Kullanıcı motoru seçince ADR (karar modeli karşılaştırması).
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
