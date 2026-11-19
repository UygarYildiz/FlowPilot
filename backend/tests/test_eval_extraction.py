"""Çıkarma ölçüm aracı (model çağrısı yok): puanlama ve kriter 5 sayımı."""

import json
from pathlib import Path

from flowpilot.core.ingestion.extract import extract_text
from flowpilot.departments.procurement.extraction import QuoteExtraction
from flowpilot.evals.extraction import DocResult, score, summarize

ROOT = Path(__file__).resolve().parents[1] / "evals" / "extraction"


def _row(doc_id: str) -> tuple[dict, str]:
    rows = [json.loads(line) for line in (ROOT / "dataset.jsonl").read_text("utf-8").splitlines()]
    row = next(r for r in rows if r["id"] == doc_id)
    data = (ROOT / "documents" / row["file"]).read_bytes()
    return row, extract_text(row["file"], "", data).text or ""


def test_dataset_has_at_least_30_documents_with_traps() -> None:
    rows = (ROOT / "dataset.jsonl").read_text("utf-8").splitlines()
    assert len(rows) >= 30
    assert sum(bool(json.loads(r)["traps"]) for r in rows) >= 5


def test_perfect_extraction_scores_all_fields_correct() -> None:
    row, text = _row("ex-001")
    is_quote, fields = score(row, QuoteExtraction.model_validate(row["expected"]), text)
    assert is_quote and fields and all(f.correct for f in fields)
    assert not any(f.flagged for f in fields)


def test_invented_amount_is_wrong_but_flagged_so_criterion_5_holds() -> None:
    row, text = _row("ex-001")
    bad = json.loads(json.dumps(row["expected"]))
    bad["lines"][0]["unit_price"] = 12345.67  # belgede yok
    _, fields = score(row, QuoteExtraction.model_validate(bad), text)
    wrong = [f for f in fields if not f.correct]
    assert [f.field for f in wrong] == ["lines[0].unit_price"] and wrong[0].flagged
    result = DocResult("ex-001", row["file"], row["layout"], [], True, fields)
    assert result.unflagged_wrong_amounts == []
    summary = summarize([result])
    assert summary["wrong_amounts"] == 1 and summary["unflagged_wrong_amounts"] == 0


def test_non_quote_document_is_scored_on_is_quote_only() -> None:
    row = next(
        json.loads(r)
        for r in (ROOT / "dataset.jsonl").read_text("utf-8").splitlines()
        if not json.loads(r)["expected"]["is_quote"]
    )
    is_quote_correct, fields = score(row, QuoteExtraction(is_quote=False), "")
    assert is_quote_correct and fields == []
