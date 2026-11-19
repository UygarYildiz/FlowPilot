"""Satın Alma departmanı (v1: ajanlı — ajan M5'te eklenecek)."""

from flowpilot.core.registry import Department, Intent

DEPARTMENT = Department(
    key="procurement",
    name="Satın Alma",
    description=(
        "Tedarikçilerle ilişkiler ve şirketin dışarıdan mal/hizmet alımı: tedarikçi teklifleri, "
        "fiyat listeleri, satın alma talepleri, tedarikçiye verilen siparişler."
    ),
    intents=(
        Intent(
            "new_quote",
            "Bir tedarikçi şirketimize fiyat teklifi gönderiyor (çoğunlukla PDF/Excel ekli).",
            ("SAT-2026-031 talebiniz için fiyat teklifimiz ektedir.",),
        ),
        Intent(
            "price_update",
            "Bir tedarikçi fiyat listesini veya ürün fiyatlarını güncelliyor.",
            ("1 Aralık itibarıyla geçerli güncel fiyat listemiz ektedir.",),
        ),
        Intent(
            "order_status_inquiry",
            "Bir tedarikçi, şirketimizin ona verdiği siparişin durumunu soruyor ya da teyit "
            "istiyor.",
            ("PO-2026-0902 siparişinin imzalı formu bize ulaşmadı, teyit eder misiniz?",),
        ),
        Intent(
            "supplier_complaint",
            "Bir tedarikçi şikâyet, itiraz veya anlaşmazlık bildiriyor.",
            ("Şartname değişikliği bize yazılı bildirilmedi ve ek maliyet doğurdu.",),
        ),
        Intent(
            "purchase_request",
            "Şirket içinden bir birim malzeme veya hizmet satın alınmasını talep ediyor.",
            ("Hat 3 bakımı için 2 adet pompa ve 12 filtre gerekiyor.",),
        ),
    ),
)
