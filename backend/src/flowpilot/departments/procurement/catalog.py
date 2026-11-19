"""Demo ürün kataloğu ve sabit demo kurları (kurgusal; ADR-015).

Katalog yalnızca uyarı üretir: kodu katalogda olmayan satır kaydedilebilir ama işaretlenir.
"""

from decimal import Decimal

PRODUCTS: dict[str, str] = {
    # Rulmanlar
    "RLM-6205-2RS": "Sabit bilyalı rulman 6205-2RS",
    "RLM-6206-2RS": "Sabit bilyalı rulman 6206-2RS",
    "RLM-6308-ZZ": "Sabit bilyalı rulman 6308-ZZ",
    "RLM-6310-ZZ": "Sabit bilyalı rulman 6310-ZZ",
    "RLM-32210": "Konik makaralı rulman 32210",
    "RLM-22216": "Oynak makaralı rulman 22216",
    # Hidrolik
    "HYD-PMP-045": "Dişli pompa 45 cc",
    "HYD-VLF-12": 'Yön kontrol valfi 1/2"',
    "HYD-HRT-08": "Hidrolik hortum 8 mm",
    "HYD-FLT-10": "Dönüş filtresi 10 mikron",
    "HYD-SIL-63": "Hidrolik silindir 63/36",
    # Güç aktarma
    "KPL-N-095": "Kaplin N-Eupex 95",
    "KPL-N-125": "Kaplin N-Eupex 125",
    "KYS-SPZ-1250": "V kayışı SPZ 1250",
    "KYS-SPB-2000": "V kayışı SPB 2000",
    "ZNC-08B-1": "Makaralı zincir 08B-1 (5 m)",
    # Konveyör
    "KNV-MKR-89": "Konveyör makarası Ø89",
    "KNV-BNT-650": "Konveyör bandı 650 mm (m)",
    "MTR-RDK-4KW": "Redüktörlü motor 4 kW",
    "SNS-IND-M18": "İndüktif sensör M18",
}

# Sabit demo kurları (1 birim = ? TRY). Gerçek kur değildir; karşılaştırma tek para biriminde
# yapılsın diye.
DEMO_FX_TRY: dict[str, Decimal] = {
    "TRY": Decimal("1"),
    "EUR": Decimal("37.50"),
    "USD": Decimal("34.80"),
}
