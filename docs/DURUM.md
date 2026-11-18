# Durum — nerede kaldık?

> Her çalışma oturumunun sonunda güncellenir. Bu dosya **kısa** kalır (en fazla ~60 satır).
> Geçmiş burada birikmez: biten işler `gunluk/` ve `CHANGELOG.md`'ye gider.

**Son güncelleme:** 2026-11-18
**Aktif sürüm:** v1 — Çekirdek + Procurement ([kapsam](surumler/v1.md))
**Aşama:** M0 (iskelet) ve M1 (e-posta girişi) bitti; M2 (karar) başlamadı.
**Yığın:** ADR-009 — Python/FastAPI, PostgreSQL, React/Vite, LLM olarak Gemini (ücretsiz katman).
**Uzak depo:** https://github.com/UygarYildiz/FlowPilot (`main`, CI: GitHub Actions)

## Şu an yapılan
- Yok. Sıradaki adımı bekliyor.

## Sıradaki adım (M2)
1. Departman sözleşmesi + kayıt defteri; 4 departman (yalnızca `key/name/intents`). import-linter'a kural 2'yi ekle.
2. `Decision` / `Route` modelleri + göç; Decision Engine (şema doğrulama, eşik 0.75, bir yeniden deneme, manuel inceleme).
3. `llm/gemini.py` (google-genai, yapılandırılmış çıktı). Kullanıcıdan `GEMINI_API_KEY` gerekecek.
4. Yönlendirme seti (≥150 etiketli e-posta; seed'deki 15'ten başla) ve ölçüm aracı.

## Açık sorular
- Kullanılacak Gemini modeli (M2'de değerlendirme setiyle seçilecek; ücretsiz katman sınırlarına bakılacak).
- Panel dili: Türkçe mi, İngilizce mi (başvurulacak ilanlara göre)?

## Notlar
- Gemini ücretsiz katmanına yalnızca kurgusal veri gönderilir (ADR-009).
- Geliştirme veritabanı `localhost:5433` (5432'de makinede başka bir PostgreSQL var). Testler `flowpilot_test` veritabanını kendisi kurar.
- IMAP adaptörü yalnızca sahte sunucuyla test edildi; gerçek posta kutusuyla denenmedi.

## Engeller
- Yok.
