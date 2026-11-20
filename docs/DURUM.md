# Durum — nerede kaldık?

> Her çalışma oturumunun sonunda güncellenir. Bu dosya **kısa** kalır (en fazla ~60 satır).
> Geçmiş burada birikmez: biten işler `gunluk/` ve `CHANGELOG.md`'ye gider.

**Son güncelleme:** 2026-11-20 (3)
**Aktif sürüm:** v1 — Çekirdek + Procurement ([kapsam](surumler/v1.md))
**Aşama:** M0–M5 bitti. M5: Procurement Agent beş intent (ADR-015 `new_quote`; ADR-016 `price_update`,
`order_status_inquiry`, `supplier_complaint`, `purchase_request`). Sırada M6 (yayın).
**Yığın:** ADR-009 — Python/FastAPI, PostgreSQL, React/Vite. Sınıflandırma: ADR-013 kademeli — SubQ `subq-snap-1.2` → Gemini `gemini-3.5-flash-lite` → insan.
**Uzak depo:** https://github.com/UygarYildiz/FlowPilot (`main`, CI: GitHub Actions)

## Son ölçüm (kademeli motor, test yarısı 74 e-posta, canlı, 2026-11-19)
Departman %97,3 (hedef ≥90) · otomatik yönlendirilenlerde hata %1,5 (≤5; 1 e-posta) · Procurement intent %100 (≥85)
· tüm intent %97,3 · çok departmanlı geri çağırma %100 · manuel inceleme %10,8. SubQ 58 e-postada karar verdi
(52 otomatik), Gemini 16'da (14 otomatik): Gemini çağrısı tek başına Gemini'ye göre ~%78 az.
Rapor: `backend/evals/results/routing-20261119-150223-cascade-*.md`. Tek otomatik hata ev-107: SubQ doğru ama
emin değildi (Satış %59); Gemini bu sefer Lojistik'i %85 ile ekledi (önceki çalıştırmada %60 → inceleme).
Gemini'nin güveni çalıştırmadan çalıştırmaya değişiyor.

## Çıkarma ölçümü (30 belge, `quote-extract-v1`, Gemini, 2026-11-20)
Alan doğruluğu %98,7 (762 alan; hedef ≥90) · işaretsiz yanlış tutar 0 (hedef 0) · tutar doğruluğu %100 ·
teklif/değil %100 · yanlış alarm 10 (hepsi tuzaklardaki doğru işaretler). Hatalar yalnızca `lead_time_days`
boş bırakma (3 belge; çalıştırmadan çalıştırmaya değişiyor). Rapor: `evals/results/extraction-20261119-215718-*`.
Set betikle üretilir (`scripts/make_extraction_set.py`); dev/test bölmesi yok, prompt ayarı yapılmadı.

## Motor karşılaştırması (özet; ayrıntı `gunluk/2026-11.md` 6–12, ADR-013)
Test yarısı: Gemini %97,3 / otomatik hata %0 / inceleme %12,2 · SubQ %95,9 / %0 / %29,7 · Clef-flash %71,6 · Clef %77,0.
150 e-posta: Gemini 4 yanlış otomatik, SubQ 0. SubQ kalibre (p 0,50–0,75 → %53 doğru); Gemini neredeyse hep ≥0,9 der.
Denenip bırakılanlar: "belirsiz" eşiğini gevşetmek, `typed-v3` (asıl + ek departman soruları).

## Sıradaki adım
Kullanıcı kararı (2026-11-20, 3. oturum): yayın (deploy) sonraya; önce sistem gerçek posta kutusuyla uçtan uca
çalışmalı. M6'nın ilk parçası:
1. Otomatik işleme döngüsü (`flowpilot worker`): N saniyede bir IMAP → sınıflandırma → ajan; e-posta başına
   süre kaydı (kriter 10, p95 ≤ 60 sn). Bugün üç ayrı elle çalıştırılan komut var (`ingest imap`, `classify`,
   `agents`). IMAP her seferinde son N günü tamamen indiriyor (tekrar önleme sonra); Message-ID/UID ile
   önceden eleme düşünülmeli.
2. Kullanıcı ayrı bir test Gmail hesabı açar (2 adımlı doğrulama + uygulama şifresi) ve `backend/.env`'e
   `FLOWPILOT_IMAP_*` yazar. Kendi posta kutusu değil: Gemini ücretsiz katmanına yalnızca kurgusal veri (ADR-009).
3. Kullanıcı kendi hesabından seed'deki kurgusal e-postaları (ekliler dahil) gönderir; panelde izlenir.
4. Sonra: demo hesabı, "demo verisini sıfırla", paneli FastAPI'den sunma, README/GIF, CHANGELOG `v1.0.0`, yayın.
5. (İleride) Ajan sürümü değişince tamamlanmış `agent_run`'ları yeniden çalıştırma yolu yok. `decision-v2` denemesi.

## Açık sorular
- Canlı demonun barındırılacağı yer: ADR-009 Render diyor; kullanıcı yayını gerçek posta denemesinden sonraya bıraktı.
- Panel dili Türkçe yapıldı (ADR-012); kullanıcı İngilizce isterse `frontend/src/lib/text.ts` + sayfalar çevrilir.
- Değerlendirme setine kullanıcının da (Claude dışında) birkaç gerçekçi e-posta eklemesi ölçümü daha güvenilir yapar.

## Notlar
- 86a0f88 başka oturumun yarım M6 işini (`worker.py`, `imap.py` eklemeleri) yanlışlıkla push etmişti; sonraki
  commit bunları yalnızca depoda geri aldı (çalışma klasöründe duruyorlar, M6 işi bitince commit'lenecek).
- Commit edilmemiş: `make_extraction_set.py` biçimlendirmesi + yeniden üretilmiş 20 çıkarma belgesi (önceki oturum; içerik aynı, ~1 bayt fark). Bir sonraki commit'e girer.
- Panel yerelde: `.claude/launch.json` (api :8000, panel :5173). Demo hesaplar `uv run flowpilot users demo`, şifre `flowpilot-demo`.
- Tarayıcı denemeleri geliştirme veritabanını değiştirdi (1 e-posta kapatıldı, 1 düzeltildi, 1 rota kapatıldı). Sıfırlama komutu yok (M6).
- Kullanıcıya her oturum sonunda `ILERLEME.md` sade dille güncellenir (ADR-011); Stop/pre-commit kontrolü ister.
- Gemini ücretsiz katmanına yalnızca kurgusal veri gönderilir (ADR-009). `.env` gitignore'da.
- Docker Desktop kapanınca DB testleri atlanır (yerelde); `docker compose up -d` gerekir. DB `localhost:5433`.
- IMAP adaptörü yalnızca sahte sunucuyla test edildi.
- Geliştirme DB'si (2026-11-20): göç `b3e23afd5d95` uygulandı. M4'teki geçici deneme ajanının çalışması ve 3 önerisi
  silindi (denetim olayları duruyor); gerçek ajan çalıştı: Anadolu ve Özkan teklifleri + SAT-2026-031 taslağı onaylı.
  2. parça: göç `b7f029c4be61`; 4 boş `agent_run` silinip ajan yeniden çalıştı; şikâyet yanıtı onaylı, diğer
  üç öneri (fiyat güncellemesi, sipariş durumu yanıtı, iç talep) kullanıcı için bekliyor.
- `flowpilot agents`: açık rotalarda ajanları çalıştırır; Satın Alma ajanı modeli `FLOWPILOT_LLM_PROVIDER`'dan alır.
- `backend/.env`: `FLOWPILOT_DECISION_ENGINE=cascade`, `FLOWPILOT_LLM_PROVIDER=gemini` (önceden `fake`); `SUBQ_API_KEY` dolu.
  Kademeli kararla paneldeki fiş tarayıcıda görülmedi (geliştirme DB'sinde bekleyen e-posta yoktu).

## Engeller
- Yok.
