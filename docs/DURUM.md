# Durum — nerede kaldık?

> Her çalışma oturumunun sonunda güncellenir. Bu dosya **kısa** kalır (en fazla ~60 satır).
> Geçmiş burada birikmez: biten işler `gunluk/` ve `CHANGELOG.md`'ye gider.

**Son güncelleme:** 2026-11-18
**Aktif sürüm:** v1 — Çekirdek + Procurement ([kapsam](surumler/v1.md))
**Aşama:** M0 (iskelet) bitti; M1 (giriş) başlamadı.
**Yığın:** ADR-009 — Python/FastAPI, PostgreSQL, React/Vite, LLM olarak Gemini (ücretsiz katman).
**Uzak depo:** https://github.com/UygarYildiz/FlowPilot (`main`, CI: GitHub Actions)

## Şu an yapılan
- Yok. Sıradaki adımı bekliyor.

## Sıradaki adım
1. M1: SQLAlchemy veri modeli + Alembic ilk göç (`Email`, `Attachment`, `AuditEvent`, `User`).
2. Giriş adaptörü arayüzü; seed adaptörü + ilk kurgusal e-postalar (Atlas Endüstri); IMAP adaptörü.
3. Ek metni çıkarma (pdfplumber, openpyxl), tekrar önleme testi (başarı kriteri 6).

## Açık sorular
- Kullanılacak Gemini modeli (M2'de değerlendirme setiyle seçilecek; ücretsiz katman sınırlarına bakılacak).
- Panel dili: Türkçe mi, İngilizce mi (başvurulacak ilanlara göre)?

## Notlar
- Gemini ücretsiz katmanına yalnızca kurgusal veri gönderilir (ADR-009).
- MIMARI.md kural 2'nin import-linter sözleşmesi ilk departman paketiyle (M2) eklenecek.

## Engeller
- Yok.
