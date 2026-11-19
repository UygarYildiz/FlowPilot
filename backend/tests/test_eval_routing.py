from pathlib import Path

from conftest import BACKEND, SEED_DIR

from flowpilot.bootstrap import get_registry
from flowpilot.core.decision.engine import Classification
from flowpilot.core.decision.schema import ModelRoute
from flowpilot.evals import routing

DATASET = BACKEND / "evals" / "routing" / "dataset.jsonl"


def _classification(*routes: tuple[str, str | None], review: bool = False) -> Classification:
    return Classification(
        routes=[
            ModelRoute(
                department=d, intent=i, priority="normal", confidence=0.9, suggested_action=""
            )
            for d, i in routes
        ],
        reasoning="",
        needs_review=review,
        review_reason=None,
        attempts=1,
    )


def test_dataset_loads_and_labels_are_valid() -> None:
    cases = routing.load_cases(DATASET, SEED_DIR)
    assert len(cases) >= 50
    registry = get_registry()
    for case in cases:
        for department, intent in case.expected.items():
            if department == "unknown":
                assert intent is None and len(case.expected) == 1, case.id
                continue
            dept = registry.get(department)
            assert dept is not None and intent in dept.intent_keys(), case.id
        assert all(registry.get(d) for d in case.acceptable), case.id


def test_seed_cases_include_attachment_text() -> None:
    [case] = [c for c in routing.load_cases(DATASET, SEED_DIR) if c.id == "seed-001"]
    assert case.email.attachments[0].text and "RLM-6205-2RS" in case.email.attachments[0].text


def _case(
    expected: dict[str, str | None], acceptable: frozenset[str] = frozenset()
) -> routing.Case:
    [seed] = [c for c in routing.load_cases(DATASET, SEED_DIR) if c.id == "seed-013"]
    return routing.Case("x", seed.email, expected, acceptable)


def test_score_requires_all_expected_and_allows_acceptable_extras() -> None:
    case = _case(
        {"logistics": "delivery_issue", "finance": "invoice_dispute"}, frozenset({"sales_orders"})
    )
    full = routing.score(
        case,
        _classification(
            ("logistics", "delivery_issue"),
            ("finance", "invoice_dispute"),
            ("sales_orders", "customer_request"),
        ),
    )
    assert full.department_correct and all(full.intent_correct.values())

    missing = routing.score(case, _classification(("logistics", "delivery_issue")))
    assert not missing.department_correct

    extra = routing.score(
        _case({"finance": "invoice_dispute"}),
        _classification(("finance", "invoice_received"), ("procurement", "new_quote")),
    )
    assert not extra.department_correct
    assert extra.intent_correct == {"finance": False}


def test_summary_metrics(tmp_path: Path) -> None:
    good = routing.score(
        _case({"procurement": "new_quote"}), _classification(("procurement", "new_quote"))
    )
    wrong_auto = routing.score(
        _case({"finance": "invoice_received"}), _classification(("procurement", "new_quote"))
    )
    right_review = routing.score(
        _case({"unknown": None}), _classification(("unknown", None), review=True)
    )
    summary = routing.summarize([good, wrong_auto, right_review])
    assert summary["department_accuracy"] == 2 / 3
    assert summary["auto_routed"] == 2 and summary["auto_routed_error_rate"] == 0.5
    assert summary["procurement_intent"] == 1.0
    assert summary["review_that_was_correct"] == 1

    meta = {"model": "fake", "date": "-", "dataset": "d", "prompt_version": "v", "threshold": 0.75}
    report = routing.write_report(tmp_path, summary, [good, wrong_auto, right_review], meta)
    text = report.read_text(encoding="utf-8")
    assert "❌ hedef ≥ %90.0" in text and "**x**" in text
    assert report.with_suffix(".json").exists()
