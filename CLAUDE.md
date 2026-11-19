# FlowPilot — çalışma kuralları

AI destekli e-posta yönlendirme ve departman ajanı platformu. Departman departman artırımlı geliştirilir (ADR-001).

## Oturum başında
Aşağıdaki durum dosyası otomatik yüklenir; işe oradan başla. Gerekirse YOL_HARITASI.md ve ilgili ADR'leri oku.

@docs/DURUM.md

## Belge sistemi — hangi bilgi nereye
| Bilgi | Dosya | Kural |
|---|---|---|
| Kullanıcı için sade ilerleme özeti | `ILERLEME.md` | Teknik olmayan dille: sistem bugün ne yapıyor, yol haritasında neredeyiz, son oturumlar, sırada ne var, kullanıcıdan beklenenler. Üzerine yazılır; "Son oturumlar" en fazla 3 kayıt, eskisi günlüğe kalır. |
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
  1. `ILERLEME.md`: kullanıcının projeden kopmaması için, jargon kullanmadan (gerekirse sözlüğe terim ekle).
  2. `docs/DURUM.md`: tarih, şu an yapılan, sıradaki adım, açık sorular.
  3. `docs/gunluk/<bu ay>.md`: en üste kısa kayıt.
  4. Mimari değiştiyse `docs/MIMARI.md`; bir seçenek seçildiyse `docs/KARARLAR.md`'ye ADR.
  5. Yol haritasındaki maddenin işaretini güncelle.
- Belgeler kodla **aynı commit'te** güncellenir.
- İki kontrol `docs/DURUM.md` ve `ILERLEME.md` güncellemesini zorlar: Claude Code Stop hook'u (`.claude/hooks/dokuman-kontrol.mjs`) ve git pre-commit hook'u (`.githooks/pre-commit`). Hook uyarırsa belgeleri güncelle; kontrolü atlatmaya çalışma.
- Yalnızca soru-cevap veya okuma yapılan oturumlarda belge güncellenmez.

## Oturum sonu mesajı
Kullanıcıya kapanış mesajı `ILERLEME.md` ile aynı dilde yazılır: önce sade bir özet (bu oturumda sistem ne
kazandı, bir örnekle), sonra yol haritasında neredeyiz (M0–M6), sonra kullanıcıdan beklenen karar. Teknik
ayrıntı (dosya adları, sınıflar, hata türleri) yalnızca gerekiyorsa ve en sonda, kısa.

## Karmaşıklığı önleme
- MIMARI.md'deki bağımlılık kurallarına uy; bir kuralı çiğnemek gerekiyorsa önce ADR yaz.
- Yeni departman çekirdeğe dokunmadan eklenir (ADR-004). Dokunmak gerekiyorsa dur ve kullanıcıya sor.
- Aktif sürümün kapsamı dışında iş yapma; fikir çıkarsa DURUM.md'deki açık sorulara veya YOL_HARITASI.md'nin "Sonrası" bölümüne yaz.
- Bu dosya kısa kalır: ayrıntı buraya değil, ilgili belgeye yazılır.

## Dil
Belgeler, commit mesajları ve kullanıcıya yazılanlar Türkçe. Kod tanımlayıcıları İngilizce.
