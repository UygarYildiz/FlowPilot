"""Lojistik departmanı (v1: ajansız, manuel işlenir; ajan v4'te)."""

from flowpilot.core.registry import Department, Intent

DEPARTMENT = Department(
    key="logistics",
    name="Lojistik",
    description=(
        "Malların fiziksel hareketi: sevkiyat planlama, nakliye/kargo firmalarıyla iletişim, "
        "teslimat gecikmeleri, eksik veya hasarlı teslimatlar, irsaliyeler."
    ),
    intents=(
        Intent(
            "shipment_request",
            "Bir sevkiyat için araç, nakliye veya gönderim planlaması isteniyor.",
            ("6 palet ürün yarın yüklemeye hazır, kapalı kasa araç ayarlayabilir misiniz?",),
            label="Sevkiyat talebi",
        ),
        Intent(
            "delivery_delay",
            "Bir nakliye firması veya taraf sevkiyatın gecikeceğini bildiriyor.",
            ("HL-55120 sevkiyatınız yol çalışması nedeniyle bugün teslim edilemeyecek.",),
            label="Teslimat gecikmesi",
        ),
        Intent(
            "delivery_issue",
            "Teslimatta eksik, fazla veya hasarlı ürün bildiriliyor.",
            ("Dünkü teslimatta 2 adet kaplin eksik geldi.",),
            label="Teslimat sorunu",
        ),
        Intent(
            "shipping_info",
            "Takip numarası, irsaliye, gümrük veya sevkiyat belgesi paylaşılıyor ya da isteniyor.",
            ("Sevkiyatın takip numarası ve irsaliyesi ektedir.",),
            label="Sevkiyat bilgisi/belgesi",
        ),
    ),
)
