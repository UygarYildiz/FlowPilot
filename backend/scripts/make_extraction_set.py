"""Teklif çıkarma ölçüm setini üretir (v1 kapsamı 3.7, ADR-015): evals/extraction/.

30 kurgusal teklif belgesi (PDF/XLSX/CSV, 6 farklı düzen) ve her biri için beklenen alanlar.
Beklenen değer her zaman BELGEDE YAZANDIR (tedarikçi hata yapmışsa hatalı değer); doğrulamanın
o hatayı yakalaması ayrıca ölçülür. Rastgelelik sabit tohumludur: betik aynı seti üretir.

    uv run python scripts/make_extraction_set.py
PDF'lerde Türkçe karakterler için TTF yazı tipi gerekir (varsayılan: Windows Arial; SEED_FONT).
"""

import csv
import json
import os
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import openpyxl
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1] / "evals" / "extraction"
DOCS = ROOT / "documents"
FONT = Path(os.environ.get("SEED_FONT", r"C:\Windows\Fonts\arial.ttf"))
FONT_BOLD = Path(os.environ.get("SEED_FONT_BOLD", r"C:\Windows\Fonts\arialbd.ttf"))
CENT = Decimal("0.01")

SUPPLIERS = [
    ("Özkan Rulman San. ve Tic. Ltd. Şti.", "ozkanrulman.example"),
    ("Anadolu Rulman A.Ş.", "anadolurulman.example"),
    ("Kaya Hidrolik Makina Ltd. Şti.", "kayahidrolik.example"),
    ("Ege Güç Aktarma A.Ş.", "egeguc.example"),
    ("Marmara Konveyör Sistemleri", "marmarakonveyor.example"),
    ("Bosphorus Industrial Supply Ltd.", "bosphorus-supply.example"),
    ("Delta Otomasyon ve Sensör", "deltaotomasyon.example"),
    ("Karadeniz Zincir San. A.Ş.", "karadenizzincir.example"),
]
PRODUCTS = [
    ("RLM-6205-2RS", "Sabit bilyalı rulman 6205-2RS", "adet", 68.5),
    ("RLM-6206-2RS", "Sabit bilyalı rulman 6206-2RS", "adet", 84.0),
    ("RLM-6310-ZZ", "Sabit bilyalı rulman 6310-ZZ", "adet", 318.0),
    ("RLM-22216", "Oynak makaralı rulman 22216", "adet", 2140.0),
    ("HYD-PMP-045", "Dişli pompa 45 cc", "adet", 8420.0),
    ("HYD-HRT-08", "Hidrolik hortum 8 mm", "m", 104.5),
    ("HYD-SIL-63", "Hidrolik silindir 63/36", "adet", 6950.0),
    ("KPL-N-095", "Kaplin N-Eupex 95", "adet", 1875.0),
    ("KYS-SPZ-1250", "V kayışı SPZ 1250", "adet", 142.0),
    ("ZNC-08B-1", "Makaralı zincir 08B-1 (5 m)", "takım", 655.0),
    ("KNV-MKR-89", "Konveyör makarası Ø89", "adet", 412.0),
    ("KNV-BNT-650", "Konveyör bandı 650 mm", "m", 1290.0),
    ("SNS-IND-M18", "İndüktif sensör M18", "adet", 735.0),
    ("ATL-OZEL-77", "Özel imalat burç (çizime göre)", "adet", 96.0),  # katalogda yok
]
FX = {"TRY": Decimal(1), "EUR": Decimal("37.5"), "USD": Decimal("34.8")}
CURRENCY_LABEL = {"TRY": "TL", "EUR": "EUR", "USD": "USD"}


@dataclass
class Line:
    code: str
    desc: str
    unit: str
    qty: int | None
    price: Decimal
    lead: int

    @property
    def total(self) -> Decimal:
        return (Decimal(self.qty or 0) * self.price).quantize(CENT, ROUND_HALF_UP)


@dataclass
class Spec:
    id: str
    layout: str
    supplier: str
    domain: str
    quote_no: str
    request_no: str
    issued: date
    valid_until: date
    currency: str
    lines: list[Line]
    show_currency: bool = True
    show_line_totals: bool = True
    show_totals: bool = True
    lead_in_weeks: bool = False
    wrong_line_total: int | None = None  # tedarikçinin yazım hatası: bu satırın tutarı yanlış
    wrong_grand_total: bool = False
    not_a_quote: bool = False
    traps: list[str] = field(default_factory=list)

    def shown_line_total(self, index: int) -> Decimal:
        total = self.lines[index].total
        return total + Decimal(100) if index == self.wrong_line_total else total

    @property
    def subtotal(self) -> Decimal:
        return sum((line.total for line in self.lines), Decimal(0))

    @property
    def vat(self) -> Decimal:
        return (self.subtotal * Decimal("0.20")).quantize(CENT, ROUND_HALF_UP)

    @property
    def grand_total(self) -> Decimal:
        value = self.subtotal + self.vat
        return value + Decimal(1000) if self.wrong_grand_total else value


def tr(value: Decimal | int) -> str:
    return f"{Decimal(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def en(value: Decimal | int) -> str:
    return f"{Decimal(value):,.2f}"


def lead_text(spec: Spec, line: Line) -> str:
    return f"{max(1, line.lead // 7)} hafta" if spec.lead_in_weeks else f"{line.lead} gün"


# ---------- Düzenler ----------


def _pdf() -> FPDF:
    pdf = FPDF()
    pdf.add_font("Base", "", str(FONT))
    pdf.add_font("Base", "B", str(FONT_BOLD))
    pdf.add_page()
    pdf.set_font("Base", size=10)
    return pdf


def pdf_table(spec: Spec, path: Path) -> None:
    pdf = _pdf()
    pdf.set_font("Base", "B", 14)
    pdf.cell(0, 10, spec.supplier, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Base", "", 10)
    head = ["FİYAT TEKLİFİ" if not spec.not_a_quote else "SEVK İRSALİYESİ"]
    head.append(f"Belge No: {spec.quote_no}        Tarih: {spec.issued:%d.%m.%Y}")
    head.append(f"Müşteri: Atlas Endüstri A.Ş. — Talep No: {spec.request_no}")
    if not spec.not_a_quote:
        cur = f"   Para birimi: {CURRENCY_LABEL[spec.currency]}" if spec.show_currency else ""
        head.append(f"Geçerlilik: {spec.valid_until:%d.%m.%Y}{cur}")
    for text in head:
        pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    header = ["Kod", "Ürün", "Miktar", "Birim fiyat", "Tutar", "Teslim"]
    widths = [30, 62, 22, 26, 28, 20]
    if spec.not_a_quote:
        header, widths = ["Kod", "Ürün", "Sevk miktarı", "Koli"], [34, 90, 34, 30]
    pdf.set_font("Base", "B", 9)
    for text, width in zip(header, widths, strict=True):
        pdf.cell(width, 7, text, border=1)
    pdf.ln()
    pdf.set_font("Base", "", 9)
    for i, line in enumerate(spec.lines):
        if spec.not_a_quote:
            row = [line.code, line.desc, f"{line.qty} {line.unit}", str(1 + (line.qty or 0) // 50)]
        else:
            row = [
                line.code,
                line.desc,
                f"{line.qty} {line.unit}",
                tr(line.price),
                tr(spec.shown_line_total(i)) if spec.show_line_totals else "",
                lead_text(spec, line),
            ]
        for text, width in zip(row, widths, strict=True):
            pdf.cell(width, 7, text, border=1)
        pdf.ln()
    if spec.show_totals and not spec.not_a_quote:
        unit = f" {CURRENCY_LABEL[spec.currency]}" if spec.show_currency else ""
        pdf.ln(3)
        pdf.cell(0, 6, f"Ara toplam: {tr(spec.subtotal)}{unit}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"KDV (%20): {tr(spec.vat)}{unit}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Genel toplam: {tr(spec.grand_total)}{unit}", new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def pdf_prose(spec: Spec, path: Path) -> None:
    pdf = _pdf()
    unit = CURRENCY_LABEL[spec.currency] if spec.show_currency else ""
    paragraphs = [
        spec.supplier,
        f"Sayın Atlas Endüstri Satın Alma Birimi,",
        f"{spec.request_no} numaralı talebiniz için {spec.quote_no} numaralı teklifimizi aşağıda sunarız.",
        "",
    ]
    for line in spec.lines:
        qty = f"{line.qty} {line.unit} " if line.qty is not None else ""
        paragraphs.append(
            f"- {qty}{line.desc} ({line.code}): birim fiyat {tr(line.price)} {unit}, "
            f"teslim {lead_text(spec, line)}.".replace("  ", " ")
        )
    paragraphs += [
        "",
        "Fiyatlarımıza KDV dahil değildir.",
        f"Teklifimiz {spec.valid_until:%d.%m.%Y} tarihine kadar geçerlidir.",
        "Saygılarımızla,",
    ]
    for text in paragraphs:
        pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def xlsx_plain(spec: Spec, path: Path) -> None:
    """Anadolu düzeni: sayılar hücrede sayı, satır tutarı ve toplam yok."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Teklif"
    ws.append([f"{spec.supplier} — Fiyat Teklifi"])
    ws.append(["Teklif No", spec.quote_no])
    ws.append(["Talep No", spec.request_no])
    ws.append(["Geçerlilik", spec.valid_until.strftime("%d.%m.%Y")])
    if spec.show_currency:
        ws.append(["Para birimi", spec.currency])
    price_head = f"Birim fiyat ({spec.currency})" if spec.show_currency else "Birim fiyat"
    lead_head = "Teslim süresi (hafta)" if spec.lead_in_weeks else "Teslim süresi (gün)"
    ws.append(["Ürün kodu", "Açıklama", "Miktar", "Birim", price_head, lead_head])
    for line in spec.lines:
        lead = max(1, line.lead // 7) if spec.lead_in_weeks else line.lead
        ws.append([line.code, line.desc, line.qty, line.unit, float(line.price), lead])
    ws.append(["Not", "Fiyatlara KDV dahil değildir."])
    wb.save(path)


def xlsx_totals(spec: Spec, path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Proforma"
    ws.append([spec.supplier])
    ws.append(["TEKLİF", spec.quote_no, "Talep", spec.request_no])
    ws.append(["Son geçerlilik", spec.valid_until.isoformat()])
    cur = spec.currency if spec.show_currency else ""
    ws.append(["Kod", "Tanım", "Adet", "Birim", f"Fiyat {cur}".strip(), f"Tutar {cur}".strip(), "Termin"])
    for i, line in enumerate(spec.lines):
        ws.append(
            [
                line.code,
                line.desc,
                line.qty,
                line.unit,
                float(line.price),
                float(spec.shown_line_total(i)),
                lead_text(spec, line),
            ]
        )
    ws.append([])
    ws.append(["", "", "", "", "Ara toplam", float(spec.subtotal)])
    ws.append(["", "", "", "", "KDV %20", float(spec.vat)])
    ws.append(["", "", "", "", "Genel toplam", float(spec.grand_total)])
    wb.save(path)


def csv_tr(spec: Spec, path: Path) -> None:
    unit = CURRENCY_LABEL[spec.currency] if spec.show_currency else ""
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Tedarikçi", spec.supplier])
        w.writerow(["Teklif No", spec.quote_no])
        w.writerow(["Talep No", spec.request_no])
        w.writerow(["Geçerlilik", spec.valid_until.strftime("%d.%m.%Y")])
        w.writerow(["Kod", "Ürün", "Miktar", "Birim", f"Birim fiyat {unit}".strip(), "Tutar", "Teslim"])
        for i, line in enumerate(spec.lines):
            w.writerow(
                [
                    line.code,
                    line.desc,
                    line.qty,
                    line.unit,
                    tr(line.price),
                    tr(spec.shown_line_total(i)),
                    lead_text(spec, line),
                ]
            )
        w.writerow(["", "", "", "", "Ara toplam", tr(spec.subtotal)])
        w.writerow(["", "", "", "", "KDV", tr(spec.vat)])
        w.writerow(["", "", "", "", "Genel toplam", tr(spec.grand_total)])


def csv_en(spec: Spec, path: Path) -> None:
    """İngilizce, virgül ayraçlı, EN sayı biçimi; satır tutarı var, KDV yok."""
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Supplier", spec.supplier])
        w.writerow(["Quotation", spec.quote_no, "Your ref", spec.request_no])
        w.writerow(["Valid until", spec.valid_until.isoformat()])
        if spec.show_currency:
            w.writerow(["Currency", spec.currency])
        w.writerow(["Item", "Description", "Qty", "UoM", "Unit price", "Amount", "Lead time (days)"])
        for i, line in enumerate(spec.lines):
            w.writerow(
                [
                    line.code,
                    line.desc,
                    line.qty,
                    line.unit,
                    en(line.price),
                    en(spec.shown_line_total(i)),
                    line.lead,
                ]
            )
        w.writerow(["", "", "", "", "Total (excl. VAT)", en(spec.subtotal)])


LAYOUTS = {
    "pdf_table": (pdf_table, "pdf"),
    "pdf_prose": (pdf_prose, "pdf"),
    "xlsx_plain": (xlsx_plain, "xlsx"),
    "xlsx_totals": (xlsx_totals, "xlsx"),
    "csv_tr": (csv_tr, "csv"),
    "csv_en": (csv_en, "csv"),
}

# Düzene göre belgede hangi alanlar yazıyor
SHOWS = {
    "pdf_table": {"line_totals": True, "totals": True, "vat": True},
    "pdf_prose": {"line_totals": False, "totals": False, "vat": False},
    "xlsx_plain": {"line_totals": False, "totals": False, "vat": False},
    "xlsx_totals": {"line_totals": True, "totals": True, "vat": True},
    "csv_tr": {"line_totals": True, "totals": True, "vat": True},
    "csv_en": {"line_totals": True, "totals": True, "vat": False},  # yalnızca KDV hariç toplam
}


def money(value: Decimal) -> float:
    return float(value.quantize(CENT, ROUND_HALF_UP))


def expected(spec: Spec) -> dict:
    if spec.not_a_quote:
        return {"is_quote": False}
    shows = SHOWS[spec.layout]
    lines = []
    for i, line in enumerate(spec.lines):
        lines.append(
            {
                "product_code": line.code,
                "quantity": line.qty,
                "unit": line.unit,
                "unit_price": money(line.price),
                "line_total": money(spec.shown_line_total(i)) if shows["line_totals"] else None,
                "lead_time_days": None if spec.lead_in_weeks else line.lead,
            }
        )
    out = {
        "is_quote": True,
        "supplier": spec.supplier,
        "quote_no": spec.quote_no,
        "request_no": spec.request_no,
        "currency": spec.currency if spec.show_currency else None,
        "valid_until": spec.valid_until.isoformat(),
        "lines": lines,
        "subtotal": money(spec.subtotal) if shows["totals"] else None,
        "vat": money(spec.vat) if shows["vat"] else None,
        "total": money(spec.grand_total) if shows["totals"] and shows["vat"] else None,
    }
    if spec.layout == "csv_en":
        # Tek toplam satırı "Total (excl. VAT)": ara toplamdır; genel toplam yazmıyor.
        out["total"] = None
    return out


def build_specs() -> list[Spec]:
    rnd = random.Random(2026)
    layouts = list(LAYOUTS)
    specs = []
    for n in range(30):
        layout = layouts[n % len(layouts)]
        supplier, domain = SUPPLIERS[n % len(SUPPLIERS)]
        currency = "USD" if layout == "csv_en" else rnd.choice(["TRY", "TRY", "EUR"])
        chosen = rnd.sample(PRODUCTS, rnd.randint(2, 5))
        lines = []
        for code, desc, unit, base_try in chosen:
            price = (Decimal(str(base_try)) * Decimal(str(rnd.uniform(0.85, 1.2))) / FX[currency])
            price = price.quantize(CENT, ROUND_HALF_UP)
            qty = rnd.choice([5, 10, 12, 20, 24, 40, 50, 60, 100, 150, 200, 400])
            lines.append(Line(code, desc, unit, qty, price, rnd.choice([3, 5, 7, 10, 14, 21, 28])))
        issued = date(2026, 11, 2) + timedelta(days=rnd.randint(0, 14))
        spec = Spec(
            id=f"ex-{n + 1:03d}",
            layout=layout,
            supplier=supplier,
            domain=domain,
            quote_no=f"{domain[:3].upper()}-{rnd.randint(1000, 9999)}",
            request_no=f"SAT-2026-{rnd.randint(30, 80):03d}",
            issued=issued,
            valid_until=issued + timedelta(days=rnd.choice([15, 21, 30, 45])),
            currency=currency,
            lines=lines,
        )
        # Bilinçli tuzaklar
        if n == 4:
            spec.show_currency, spec.traps = False, ["para birimi yazılmamış"]
        if n == 9:
            spec.lead_in_weeks, spec.traps = True, ["teslim süresi hafta olarak"]
        if n == 14:
            spec.wrong_line_total, spec.traps = 1, ["tedarikçi satır tutarını yanlış yazmış"]
            spec.layout = "csv_tr"
        if n == 19:
            spec.not_a_quote, spec.traps = True, ["teklif değil, irsaliye"]
            spec.layout = "pdf_table"
        if n == 22:
            spec.traps = ["miktarsız fiyat teklifi"]
            for line in spec.lines:
                line.qty = None
            spec.layout = "pdf_prose"
        if n == 26:
            spec.wrong_grand_total, spec.traps = True, ["genel toplam tutmuyor"]
            spec.layout = "pdf_table"
        specs.append(spec)
    return specs


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in build_specs():
        writer, ext = LAYOUTS[spec.layout]
        filename = f"{spec.id}-{spec.layout}.{ext}"
        writer(spec, DOCS / filename)
        rows.append(
            {
                "id": spec.id,
                "file": filename,
                "sender": f"satis@{spec.domain}",
                "layout": spec.layout,
                "traps": spec.traps,
                "expected": expected(spec),
            }
        )
    with (ROOT / "dataset.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} belge: {DOCS}")


if __name__ == "__main__":
    main()
