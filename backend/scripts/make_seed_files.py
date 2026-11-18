"""Kurgusal Atlas Endüstri e-postalarının eklerini üretir (seed/atlas/attachments).

Üretilen dosyalar depoya eklenir; bu betik yalnızca ekler değiştirilmek istenirse çalıştırılır:
    uv run python scripts/make_seed_files.py
PDF'lerde Türkçe karakterler için bir TTF yazı tipi gerekir (varsayılan: Windows Arial).
"""

import csv
import os
from pathlib import Path

import openpyxl
from fpdf import FPDF

OUT = Path(__file__).resolve().parents[1] / "seed" / "atlas" / "attachments"
FONT = Path(os.environ.get("SEED_FONT", r"C:\Windows\Fonts\arial.ttf"))
FONT_BOLD = Path(os.environ.get("SEED_FONT_BOLD", r"C:\Windows\Fonts\arialbd.ttf"))

# Satın alma talebi SAT-2026-031 için iki tedarikçinin teklif ettiği kalemler.
RFQ_ITEMS = [
    ("RLM-6205-2RS", "Sabit bilyalı rulman 6205-2RS", 400, "adet"),
    ("RLM-6308-ZZ", "Sabit bilyalı rulman 6308-ZZ", 150, "adet"),
    ("RLM-32210", "Konik makaralı rulman 32210", 60, "adet"),
]


def _pdf() -> FPDF:
    pdf = FPDF()
    pdf.add_font("Base", "", str(FONT))
    pdf.add_font("Base", "B", str(FONT_BOLD))
    pdf.add_page()
    pdf.set_font("Base", size=10)
    return pdf


def _table(pdf: FPDF, header: list[str], rows: list[list[str]], widths: list[int]) -> None:
    pdf.set_font("Base", "B", 9)
    for text, width in zip(header, widths, strict=True):
        pdf.cell(width, 7, text, border=1)
    pdf.ln()
    pdf.set_font("Base", "", 9)
    for row in rows:
        for text, width in zip(row, widths, strict=True):
            pdf.cell(width, 7, text, border=1)
        pdf.ln()


def _money(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def quote_ozkan() -> None:
    pdf = _pdf()
    pdf.set_font("Base", "B", 14)
    pdf.cell(0, 10, "Özkan Rulman San. ve Tic. Ltd. Şti.", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Base", "", 10)
    for line in [
        "FİYAT TEKLİFİ",
        "Teklif No: TK-2611-07        Tarih: 17.11.2026",
        "Müşteri: Atlas Endüstri A.Ş. — Talep No: SAT-2026-031",
        "Geçerlilik: 01.12.2026        Para birimi: TRY",
        "",
    ]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    prices = {"RLM-6205-2RS": 68.50, "RLM-6308-ZZ": 214.00, "RLM-32210": 489.90}
    rows, total = [], 0.0
    for code, name, qty, unit in RFQ_ITEMS:
        amount = prices[code] * qty
        total += amount
        rows.append([code, name, f"{qty} {unit}", _money(prices[code]), _money(amount), "10 gün"])
    _table(
        pdf,
        ["Kod", "Ürün", "Miktar", "Birim fiyat", "Tutar", "Teslim"],
        rows,
        [30, 62, 22, 25, 28, 18],
    )
    pdf.ln(3)
    pdf.cell(0, 6, f"Ara toplam: {_money(total)} TRY", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"KDV (%20): {_money(total * 0.2)} TRY", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Genel toplam: {_money(total * 1.2)} TRY", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Ödeme: 30 gün vadeli. Teslim: Atlas Endüstri Gebze depo.")
    pdf.output(str(OUT / "teklif-ozkan-rulman-TK-2611-07.pdf"))


def quote_anadolu() -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Teklif"
    ws.append(["Anadolu Rulman A.Ş. — Fiyat Teklifi"])
    ws.append(["Teklif No", "AR-26-1184"])
    ws.append(["Talep No", "SAT-2026-031"])
    ws.append(["Geçerlilik", "28.11.2026"])
    ws.append(["Para birimi", "EUR"])
    ws.append([])
    ws.append(
        ["Ürün kodu", "Açıklama", "Miktar", "Birim", "Birim fiyat (EUR)", "Teslim süresi (gün)"]
    )
    prices = {"RLM-6205-2RS": 1.62, "RLM-6308-ZZ": 5.35, "RLM-32210": 11.80}
    days = {"RLM-6205-2RS": 5, "RLM-6308-ZZ": 5, "RLM-32210": 21}
    for code, name, qty, unit in RFQ_ITEMS:
        ws.append([code, name, qty, unit, prices[code], days[code]])
    ws.append([])
    ws.append(["Not", "Fiyatlara KDV dahil değildir. Navlun alıcıya aittir."])
    wb.save(OUT / "teklif-anadolu-rulman-AR-26-1184.xlsx")


def price_list_kaya() -> None:
    rows = [
        ["Ürün kodu", "Açıklama", "Eski fiyat (TRY)", "Yeni fiyat (TRY)", "Geçerlilik başlangıcı"],
        ["HYD-PMP-045", "Dişli pompa 45 cc", "7.850,00", "8.420,00", "01.12.2026"],
        ["HYD-VLF-12", 'Yön kontrol valfi 1/2"', "2.310,00", "2.310,00", "01.12.2026"],
        ["HYD-HRT-08", "Hidrolik hortum 8 mm (m)", "96,00", "104,50", "01.12.2026"],
        ["HYD-FLT-10", "Dönüş filtresi 10 mikron", "640,00", "702,00", "01.12.2026"],
    ]
    with (OUT / "fiyat-listesi-kaya-hidrolik-2026-12.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        csv.writer(f, delimiter=";").writerows(rows)


def invoice_ozkan() -> None:
    pdf = _pdf()
    pdf.set_font("Base", "B", 14)
    pdf.cell(0, 10, "Özkan Rulman San. ve Tic. Ltd. Şti.", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Base", "", 10)
    for line in [
        "e-FATURA",
        "Fatura No: OZR2026000412        Fatura tarihi: 14.11.2026",
        "Alıcı: Atlas Endüstri A.Ş.        Sipariş No: PO-2026-0877",
        "Vade: 14.12.2026",
        "",
    ]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    _table(
        pdf,
        ["Kod", "Ürün", "Miktar", "Birim fiyat", "Tutar"],
        [
            ["RLM-6204-2RS", "Sabit bilyalı rulman 6204-2RS", "300 adet", "54,20", "16.260,00"],
            ["RLM-NU-210", "Silindirik makaralı rulman NU 210", "40 adet", "612,00", "24.480,00"],
        ],
        [30, 70, 25, 30, 30],
    )
    pdf.ln(3)
    pdf.cell(0, 6, "Ara toplam: 40.740,00 TRY", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "KDV (%20): 8.148,00 TRY", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Genel toplam: 48.888,00 TRY", new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(OUT / "fatura-ozkan-rulman-OZR2026000412.pdf"))


def scanned_waybill() -> None:
    # Metin katmanı olmayan tek pikselli PNG: "okunamadı" yolunu gösterir (OCR kapsam dışı).
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
        "1f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a4f50000000049454e44ae426082"
    )
    (OUT / "irsaliye-taramasi-HL-55120.png").write_bytes(png)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    quote_ozkan()
    quote_anadolu()
    price_list_kaya()
    invoice_ozkan()
    scanned_waybill()
    print(f"Ekler üretildi: {OUT}")


if __name__ == "__main__":
    main()
