# Durum — nerede kaldık?

> Her çalışma oturumunun sonunda güncellenir. Bu dosya **kısa** kalır (en fazla ~60 satır).
> Geçmiş burada birikmez: biten işler `gunluk/` ve `CHANGELOG.md`'ye gider.

**Son güncelleme:** 2026-11-19
**Aktif sürüm:** v1 — Çekirdek + Procurement ([kapsam](surumler/v1.md))
**Aşama:** M0, M1 bitti; M2 (karar) büyük ölçüde bitti — yönlendirme seti 56/150. M3 (panel) başlamadı.
**Yığın:** ADR-009 — Python/FastAPI, PostgreSQL, React/Vite, LLM: Gemini `gemini-3.5-flash-lite` (ücretsiz katman).
**Uzak depo:** https://github.com/UygarYildiz/FlowPilot (`main`, CI: GitHub Actions)

## Son ölçüm (yönlendirme, 56 e-posta, `decision-v1`)
Departman %98,2 (hedef ≥90) · otomatik yönlendirilenlerde hata %2,1 (≤5) · Procurement intent %100 (≥85)
· manuel inceleme %14,3. Rapor: `backend/evals/results/routing-20261118-233808-*.md`.

## Şu an yapılan
- Yok. Sıradaki adımı bekliyor.

## Sıradaki adım
1. Yönlendirme setini 150'ye çıkar: yanlış adrese gelen, yarım/kısa, İngilizce, iletilmiş (FW:), çok departmanlı,
   sınırda (procurement ↔ logistics, finance ↔ sales) örnekler. Etiketleri sonuca bakmadan yaz.
2. M3 panel: API uç noktaları (inbox listesi, e-posta ayrıntısı, manuel inceleme, rota düzeltme), `User` + giriş,
   React ekranları. Rota başına durum.

## Açık sorular
- Panel dili: Türkçe mi, İngilizce mi (başvurulacak ilanlara göre)?
- Değerlendirme setine kullanıcının da (Claude dışında) birkaç gerçekçi e-posta eklemesi ölçümü daha güvenilir yapar.

## Notlar
- Kullanıcıya her oturum sonunda `ILERLEME.md` sade dille güncellenir (ADR-011); Stop/pre-commit kontrolü ister.
- Gemini ücretsiz katmanına yalnızca kurgusal veri gönderilir (ADR-009). `.env` gitignore'da.
- Docker Desktop kapanınca DB testleri atlanır (yerelde); `docker compose up -d` gerekir. DB `localhost:5433`.
- IMAP adaptörü yalnızca sahte sunucuyla test edildi.

## Engeller
- Yok.
