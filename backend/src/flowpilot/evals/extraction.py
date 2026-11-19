"""Teklif çıkarma değerlendirmesi (v1 kapsamı 3.7; kriter 4 ve 5; ADR-015).

Veri seti: `evals/extraction/dataset.jsonl` + `documents/` (betikle üretilir:
`scripts/make_extraction_set.py`). Beklenen değer belgede yazandır.

Ölçütler:
- **Alan doğruluğu** (kriter 4, ≥ %90): beklenen alanların (null beklentiler dahil) doğru
  olan oranı.
- **İşaretsiz yanlış tutar** (kriter 5, = 0): yanlış ya da uydurulmuş bir tutar (miktar,
  birim fiyat,
  satır tutarı, ara toplam, KDV, genel toplam) doğrulamada `error` ile işaretlenmeden geçti mi.
"""

import json
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from flowpilot.core.ingestion.extract import extract_text
from flowpilot.departments.procurement.extraction import (
    PROMPT_VERSION,
    QuoteExtraction,
    extract_quote,
)
from flowpilot.departments.procurement.validation import validate
from flowpilot.llm import LLMClient, LLMError

TARGETS = {"field_accuracy": 0.90, "unflagged_wrong_amounts": 0}
TOP_FIELDS = ("supplier", "quote_no", "request_no", "currency", "valid_until")
TOP_AMOUNTS = ("subtotal", "vat", "total")
LINE_FIELDS = ("product_code", "quantity", "unit_price", "line_total", "lead_time_days")
AMOUNT_FIELDS = {"quantity", "unit_price", "line_total", "subtotal", "vat", "total"}
EVAL_TODAY = date(2026, 11, 1)  # ölçümde "süresi dolmuş" uyarısı karışmasın


@dataclass
class FieldResult:
    field: str
    expected: Any
    predicted: Any
    correct: bool
    flagged: bool


@dataclass
class DocResult:
    id: str
    file: str
    layout: str
    traps: list[str]
    is_quote_correct: bool
    fields: list[FieldResult] = field(default_factory=list)
    error: str | None = None
    seconds: float = 0.0

    @property
    def unflagged_wrong_amounts(self) -> list[FieldResult]:
        return [
            f
            for f in self.fields
            if f.field.rsplit(".", 1)[-1] in AMOUNT_FIELDS
            and not f.correct
            and f.predicted is not None
            and not f.flagged
        ]


def _norm_text(value: Any) -> str:
    return re.sub(r"[^0-9a-zçğıöşü]", "", str(value or "").casefold())


def _same(field_name: str, expected: Any, predicted: Any) -> bool:
    if expected is None or predicted is None:
        return expected is None and predicted is None
    name = field_name.rsplit(".", 1)[-1]
    if name in AMOUNT_FIELDS or name == "lead_time_days":
        try:
            return abs(Decimal(str(expected)) - Decimal(repr(predicted))) <= Decimal("0.005")
        except (ArithmeticError, ValueError):
            return False
    if name == "valid_until":
        return str(expected)[:10] == str(predicted)[:10]
    return _norm_text(expected) == _norm_text(predicted)


def score(
    row: dict[str, Any], extraction: QuoteExtraction, text: str
) -> tuple[bool, list[FieldResult]]:
    expected = row["expected"]
    if not expected["is_quote"]:
        return not extraction.is_quote, []
    quote = validate(
        extraction,
        text,
        source_filename=row["file"],
        fallback_supplier="",
        today=EVAL_TODAY,
    )
    predicted = extraction.model_dump()
    results: list[FieldResult] = []
    for name in TOP_FIELDS + TOP_AMOUNTS:
        results.append(
            FieldResult(
                name,
                expected.get(name),
                predicted.get(name),
                _same(name, expected.get(name), predicted.get(name)),
                quote.flagged(name),
            )
        )
    lines = predicted.get("lines") or []
    for index, exp_line in enumerate(expected["lines"]):
        got = lines[index] if index < len(lines) else {}
        for name in LINE_FIELDS:
            key = f"lines[{index}].{name}"
            results.append(
                FieldResult(
                    key,
                    exp_line.get(name),
                    got.get(name),
                    _same(name, exp_line.get(name), got.get(name)),
                    quote.flagged(key),
                )
            )
    return bool(extraction.is_quote), results


def load(dataset: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]


def run(
    rows: list[dict[str, Any]],
    documents: Path,
    *,
    llm: LLMClient,
    progress: Callable[[int, DocResult], None] | None = None,
) -> list[DocResult]:
    results = []
    for index, row in enumerate(rows, start=1):
        path = documents / row["file"]
        text = extract_text(row["file"], "", path.read_bytes()).text or ""
        started = time.perf_counter()
        result = DocResult(row["id"], row["file"], row["layout"], row["traps"], False)
        try:
            extraction = extract_quote(
                llm,
                sender=row["sender"],
                subject=f"{row['expected'].get('request_no') or ''} fiyat teklifimiz".strip(),
                filename=row["file"],
                text=text,
            )
            result.is_quote_correct, result.fields = score(row, extraction, text)
        except LLMError as exc:
            result.error = str(exc)
        result.seconds = round(time.perf_counter() - started, 3)
        results.append(result)
        if progress:
            progress(index, result)
    return results


def summarize(results: list[DocResult]) -> dict[str, Any]:
    fields = [f for r in results for f in r.fields]
    expected_fields = sum(len(r.fields) for r in results if r.error is None) + sum(
        1 for r in results if r.error is not None
    )
    correct = sum(f.correct for f in fields)
    amounts = [f for f in fields if f.field.rsplit(".", 1)[-1] in AMOUNT_FIELDS]
    wrong_amounts = [f for f in amounts if not f.correct]
    return {
        "documents": len(results),
        "failed": sum(r.error is not None for r in results),
        "is_quote_accuracy": sum(r.is_quote_correct for r in results) / len(results)
        if results
        else None,
        "field_accuracy": correct / expected_fields if expected_fields else None,
        "fields": len(fields),
        "amount_accuracy": (len(amounts) - len(wrong_amounts)) / len(amounts) if amounts else None,
        "wrong_amounts": len(wrong_amounts),
        "wrong_amounts_flagged": sum(f.flagged for f in wrong_amounts),
        "unflagged_wrong_amounts": sum(len(r.unflagged_wrong_amounts) for r in results),
        "correct_but_flagged": sum(f.correct and f.flagged for f in fields),
        "median_seconds": sorted(r.seconds for r in results)[len(results) // 2]
        if results
        else None,
    }


def _pct(value: float | None) -> str:
    return "—" if value is None else f"%{value * 100:.1f}"


def render_markdown(summary: dict[str, Any], results: list[DocResult], meta: dict[str, Any]) -> str:
    acc_ok = (summary["field_accuracy"] or 0) >= TARGETS["field_accuracy"]
    unflagged_ok = summary["unflagged_wrong_amounts"] == TARGETS["unflagged_wrong_amounts"]
    lines = [
        f"# Teklif çıkarma değerlendirmesi — {meta['model']}",
        "",
        f"- Tarih: {meta['date']}  ·  Veri seti: `{meta['dataset']}` "
        f"({summary['documents']} belge)",
        f"- Prompt: `{meta['prompt_version']}`",
        "",
        "| Ölçüt | Değer | Hedef |",
        "|---|---|---|",
        f"| 4. Alan doğruluğu | {_pct(summary['field_accuracy'])} ({summary['fields']} alan) | "
        f"{'✅' if acc_ok else '❌'} ≥ %90 |",
        f"| 5. İşaretsiz geçen yanlış tutar | {summary['unflagged_wrong_amounts']} | "
        f"{'✅' if unflagged_ok else '❌'} 0 |",
        f"| Tutar doğruluğu | {_pct(summary['amount_accuracy'])} | |",
        f"| Yanlış tutar / doğrulamanın yakaladığı | {summary['wrong_amounts']} / "
        f"{summary['wrong_amounts_flagged']} | |",
        f"| Doğru ama işaretlenmiş alan (yanlış alarm) | {summary['correct_but_flagged']} | |",
        f"| Teklif mi değil mi doğruluğu | {_pct(summary['is_quote_accuracy'])} | |",
        f"| Model hatası (çıktı alınamadı) | {summary['failed']} | |",
        f"| Ortanca süre (belge başına) | {summary['median_seconds']} sn | |",
        "",
        "## Tuzaklı belgeler",
        "",
    ]
    for r in results:
        if r.traps:
            wrong = [f for f in r.fields if not f.correct]
            status = "✓" if r.is_quote_correct and not wrong else "✗"
            detail = ", ".join(
                f"{f.field}: {f.predicted} (beklenen {f.expected}){' ⚑' if f.flagged else ''}"
                for f in wrong
            )
            lines.append(f"- {status} **{r.id}** ({', '.join(r.traps)}) {detail}")
    lines += ["", "## Hatalı alanlar (⚑ = doğrulama işaretledi)", ""]
    any_wrong = False
    for r in results:
        if r.error:
            any_wrong = True
            lines.append(f"- **{r.id}** model hatası: {r.error}")
            continue
        wrong = [f for f in r.fields if not f.correct]
        if not r.is_quote_correct:
            wrong_text = "teklif/değil kararı yanlış"
            lines.append(f"- **{r.id}** ({r.layout}): {wrong_text}")
            any_wrong = True
        if wrong and not r.traps:
            any_wrong = True
            detail = ", ".join(
                f"{f.field}: {f.predicted} (beklenen {f.expected}){' ⚑' if f.flagged else ''}"
                for f in wrong
            )
            lines.append(f"- **{r.id}** ({r.layout}): {detail}")
    if not any_wrong:
        lines.append("Yok.")
    return "\n".join(lines) + "\n"


def write_report(
    out_dir: Path, summary: dict[str, Any], results: list[DocResult], meta: dict[str, Any]
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", meta["model"])
    path = out_dir / f"extraction-{stamp}-{slug}.md"
    path.write_text(render_markdown(summary, results, meta), encoding="utf-8")
    path.with_suffix(".json").write_text(
        json.dumps(
            {"meta": meta, "summary": summary, "results": [asdict(r) for r in results]},
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return path


def meta_for(model: str, dataset: Path) -> dict[str, Any]:
    return {
        "model": model,
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset": dataset.as_posix(),
        "prompt_version": PROMPT_VERSION,
    }
