# FlowPilot — çalışma kuralları

AI destekli e-posta yönlendirme ve departman ajanı platformu. Departman departman artırımlı geliştirilir (ADR-001).

## Oturum başında
Aşağıdaki durum dosyası otomatik yüklenir; işe oradan başla. Gerekirse YOL_HARITASI.md ve ilgili ADR'leri oku.

@docs/DURUM.md

## Belge sistemi — hangi bilgi nereye
| Bilgi | Dosya | Kural |
|---|---|---|
| Nerede kaldık, sıradaki adım, açık sorular | `docs/DURUM.md` | Üzerine yazılır, en fazla ~60 satır. Geçmiş tutmaz. |
| Ne yapıldı, neden | `docs/gunluk/YYYY-AA.md` | Oturum başına bir kayıt, en yeni üstte, yalnızca eklenir. |
| Mimari karar ve gerekçesi | `docs/KARARLAR.md` | Yeni ADR eklenir; eskiler silinmez, "Yerini ADR-00X aldı" olur. |
| Sistemin bugünkü hali | `docs/MIMARI.md` | Yalnızca var olanı anlatır; planlananlar ayrı bölümde. |
| Sürümler ve iş listesi | `docs/YOL_HARITASI.md` | Maddeler `[ ]` / `[~]` / `[x]` ile işaretlenir. |
| Departman tanımı | `docs/departmanlar/<ad>.md` | `_SABLON.md`'den kopyalanır. |
| Yayına alınan değişiklikler | `CHANGELOG.md` | Sürüm yayınlanınca; değerlendirme sonuçlarıyla. |
| Ürün fikri | `docs/VIZYON.md` | Kullanıcının fikri; yalnızca kullanıcı isterse değişir. |

## Güncel tutma — zorunlu
- Kod, yapılandırma veya mimari değiştiren her oturumun sonunda, işi bitirmeden önce:
  1. `docs/DURUM.md`: tarih, şu an yapılan, sıradaki adım, açık sorular.
  2. `docs/gunluk/<bu ay>.md`: en üste kısa kayıt.
  3. Mimari değiştiyse `docs/MIMARI.md`; bir seçenek seçildiyse `docs/KARARLAR.md`'ye ADR.
  4. Yol haritasındaki maddenin işaretini güncelle.
- Belgeler kodla **aynı commit'te** güncellenir.
- İki kontrol bunu zorlar: Claude Code Stop hook'u (`.claude/hooks/dokuman-kontrol.mjs`) ve git pre-commit hook'u (`.githooks/pre-commit`). Hook uyarırsa belgeleri güncelle; kontrolü atlatmaya çalışma.
- Yalnızca soru-cevap veya okuma yapılan oturumlarda belge güncellenmez.

## Karmaşıklığı önleme
- MIMARI.md'deki bağımlılık kurallarına uy; bir kuralı çiğnemek gerekiyorsa önce ADR yaz.
- Yeni departman çekirdeğe dokunmadan eklenir (ADR-004). Dokunmak gerekiyorsa dur ve kullanıcıya sor.
- Aktif sürümün kapsamı dışında iş yapma; fikir çıkarsa DURUM.md'deki açık sorulara veya YOL_HARITASI.md'nin "Sonrası" bölümüne yaz.
- Bu dosya kısa kalır: ayrıntı buraya değil, ilgili belgeye yazılır.

## Dil
Belgeler, commit mesajları ve kullanıcıya yazılanlar Türkçe. Kod tanımlayıcıları İngilizce.
