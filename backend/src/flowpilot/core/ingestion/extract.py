"""Ek metnini bir kez çıkarır; Decision Engine ve ajanlar aynı metni kullanır (v1 kapsamı 3.1).

Desteklenen: metin tabanlı PDF, XLSX, CSV, düz metin. Diğerleri `unsupported` olarak işaretlenir.
"""

import csv
import io
from dataclasses import dataclass
from pathlib import PurePath

import openpyxl
import pdfplumber

from flowpilot.core.models import ParseStatus

PDF = "pdf"
XLSX = "xlsx"
CSV = "csv"
TEXT = "text"

_BY_MIME = {
    "application/pdf": PDF,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": XLSX,
    "text/csv": CSV,
    "text/plain": TEXT,
}
_BY_EXT = {".pdf": PDF, ".xlsx": XLSX, ".csv": CSV, ".txt": TEXT}


@dataclass(frozen=True)
class Extraction:
    status: ParseStatus
    text: str | None = None
    error: str | None = None


def detect_kind(filename: str, mime: str) -> str | None:
    return _BY_MIME.get(mime.lower().split(";")[0].strip()) or _BY_EXT.get(
        PurePath(filename).suffix.lower()
    )


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1254"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def _pdf(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n\n".join(pages).strip()


def _xlsx(data: bytes) -> str:
    workbook = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    parts: list[str] = []
    for sheet in workbook.worksheets:
        rows = [
            "\t".join("" if cell is None else str(cell) for cell in row)
            for row in sheet.iter_rows(values_only=True)
            if any(cell is not None for cell in row)
        ]
        parts.append(f"# {sheet.title}\n" + "\n".join(rows))
    workbook.close()
    return "\n\n".join(parts).strip()


def _csv(data: bytes) -> str:
    text = _decode(data)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return "\n".join("\t".join(row) for row in csv.reader(io.StringIO(text), dialect)).strip()


def extract_text(filename: str, mime: str, data: bytes) -> Extraction:
    kind = detect_kind(filename, mime)
    if kind is None:
        return Extraction(ParseStatus.UNSUPPORTED)
    try:
        if kind == PDF:
            text = _pdf(data)
        elif kind == XLSX:
            text = _xlsx(data)
        elif kind == CSV:
            text = _csv(data)
        else:
            text = _decode(data).strip()
    except Exception as exc:  # bozuk dosya: kaydı durdurmaz, işaretlenir
        return Extraction(ParseStatus.FAILED, error=f"{type(exc).__name__}: {exc}"[:500])
    if kind == PDF and not text:
        # Metin katmanı olmayan (taranmış) PDF; OCR v1 kapsamı dışında.
        return Extraction(ParseStatus.UNSUPPORTED, error="PDF'te metin yok (taranmış olabilir)")
    return Extraction(ParseStatus.OK, text=text)
