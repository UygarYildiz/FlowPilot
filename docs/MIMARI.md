# Mimari

> Bu belge **bugün var olan** sistemi anlatır. Henüz yazılmamış parçalar yalnızca "Planlanan" bölümünde durur
> ve kod yazıldıkça yukarı taşınır. Bir bileşen değiştiğinde bu belge aynı commit'te güncellenir.

**Son güncelleme:** 2026-11-18

## Var olan
Henüz kod yok.

## Bileşenler ve sınırlar
<!-- Kod yazıldıkça her bileşen için: ne yapar, nerede durur (klasör), kime bağımlı, kim ona bağımlı. -->

## Veri akışı
<!-- Bir e-postanın girişten onaya kadar izlediği yol. Kod yazılınca diyagram eklenecek. -->

## Bağımlılık kuralları
Bu kurallar kodla birlikte testlerle de korunacak:
1. Decision Engine hiçbir departman modülünü import etmez; departmanları yalnızca sözleşme üzerinden tanır.
2. Departman modülleri birbirini import etmez.
3. Departman ajanları veriyi doğrudan değiştirmez; yalnızca öneri kaydeder. Değişikliği onaydan sonra çekirdekteki tek yürütücü uygular.
4. Yeni departman eklemek çekirdek kodda değişiklik gerektirmez. Gerektiriyorsa önce sözleşme düzeltilir (ADR ile).

## Planlanan
- **Giriş katmanı:** e-postaları ve eklerini alır, kaydeder, tekrarları ayıklar.
- **Decision Engine:** yapılandırılmış karar üretir (departman, kategori, intent, öncelik, güven skoru, önerilen işlem, onay gereksinimi). Güven düşükse manuel incelemeye gönderir.
- **Departman modülleri:** her biri kendi kategorilerini, ajanını, araçlarını ve yetkilerini sözleşmeyle tanımlar.
- **Onay ve yürütme:** önerileri insana gösterir; onaylananları tek bir yürütücü bir kez uygular; her adım denetim kaydına yazılır.
- **Panel:** merkezi inbox, departman inbox'ları, karar gerekçesi, onay/ret, düzeltme, geçmiş.
