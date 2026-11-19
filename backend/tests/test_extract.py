from conftest import SEED_DIR

from flowpilot.core.ingestion.extract import extract_text
from flowpilot.core.models import ParseStatus

ATTACHMENTS = SEED_DIR / "attachments"


def _read(name: str) -> bytes:
    return (ATTACHMENTS / name).read_bytes()


def test_pdf_text_keeps_turkish_characters() -> None:
    result = extract_text(
        "teklif.pdf", "application/pdf", _read("teklif-ozkan-rulman-TK-2611-07.pdf")
    )
    assert result.status is ParseStatus.OK
    assert result.text is not None
    assert "Özkan Rulman" in result.text
    assert "RLM-6205-2RS" in result.text
    assert "SAT-2026-031" in result.text


def test_xlsx_rows_become_tab_separated_lines() -> None:
    data = _read("teklif-anadolu-rulman-AR-26-1184.xlsx")
    result = extract_text("teklif.xlsx", "", data)
    assert result.status is ParseStatus.OK
    assert result.text is not None
    assert "AR-26-1184" in result.text
    assert "RLM-32210\tKonik makaralı rulman 32210\t60\tadet\t11.8\t21" in result.text


def test_csv_with_semicolons() -> None:
    result = extract_text("liste.csv", "text/csv", _read("fiyat-listesi-kaya-hidrolik-2026-12.csv"))
    assert result.status is ParseStatus.OK
    assert result.text is not None
    assert "HYD-PMP-045\tDişli pompa 45 cc\t7.850,00\t8.420,00" in result.text


def test_csv_in_windows_turkish_encoding() -> None:
    data = "Ürün;Fiyat\nDişli;10\n".encode("cp1254")
    result = extract_text("eski.csv", "text/csv", data)
    assert result.text == "Ürün\tFiyat\nDişli\t10"


def test_image_is_unsupported() -> None:
    result = extract_text("irsaliye.png", "image/png", _read("irsaliye-taramasi-HL-55120.png"))
    assert result.status is ParseStatus.UNSUPPORTED
    assert result.text is None


def test_corrupt_pdf_is_marked_failed() -> None:
    result = extract_text("bozuk.pdf", "application/pdf", b"%PDF-1.4 bozuk")
    assert result.status is ParseStatus.FAILED
    assert result.error


def test_kind_detected_from_extension_when_mime_is_generic() -> None:
    data = _read("fiyat-listesi-kaya-hidrolik-2026-12.csv")
    assert extract_text("liste.csv", "application/octet-stream", data).status is ParseStatus.OK


def test_semicolon_csv_keeps_turkish_decimal_commas_intact() -> None:
    data = (
        "Tedarikçi;Kaya Hidrolik Makina Ltd. Şti.\n"
        "Teklif No;KAY-2138\n"
        "Kod;Ürün;Miktar;Birim fiyat TL;Tutar\n"
        "KPL-N-095;Kaplin N-Eupex 95;150;2.216,39;332.458,50\n"
        ";;;Ara toplam;352.146,74\n"
    ).encode()
    text = extract_text("teklif.csv", "text/csv", data).text or ""
    assert "KPL-N-095\tKaplin N-Eupex 95\t150\t2.216,39\t332.458,50" in text
    assert "352.146,74" in text
