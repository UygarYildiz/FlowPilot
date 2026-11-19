"""Yönlendirme değerlendirmesi: Decision Engine'i etiketli e-postalarda çalıştırır ve ölçer.

Veri seti (JSONL, satır başına bir e-posta):
    {"id": "...", "seed": "seed-001"}                       # seed e-postasını (ekleriyle) kullan
    {"id": "...", "from": "...", "to": [...], "cc": [...], "subject": "...", "body": "...",
     "attachments": [{"filename": "...", "text": "..."}]}   # ya da satır içinde tanımla
ve her ikisinde:
    "expected": {"procurement": "new_quote", "finance": "invoice_dispute"}   # departman → intent
    "acceptable": ["sales_orders"]     # (isteğe bağlı) tahmin edilse de hata sayılmayanlar
İlgisiz e-posta: "expected": {"unknown": null}.

Ölçütler v1 kapsamı bölüm 6'daki başarı kriterleriyle eşleşir (1, 2, 3).
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from flowpilot.core.decision.engine import Classification, classify
from flowpilot.core.decision.prompt import AttachmentForDecision, EmailForDecision
from flowpilot.core.ingestion.extract import extract_text
from flowpilot.core.ingestion.sources.seed import SeedSource
from flowpilot.core.registry import UNKNOWN, DepartmentRegistry
from flowpilot.llm import LLMClient

TARGETS = {"department_accuracy": 0.90, "auto_routed_error_rate": 0.05, "procurement_intent": 0.85}


@dataclass(frozen=True)
class Case:
    id: str
    email: EmailForDecision
    expected: dict[str, str | None]
    acceptable: frozenset[str] = frozenset()


@dataclass
class CaseResult:
    id: str
    expected: dict[str, str | None]
    predicted: dict[str, str | None]
    confidences: dict[str, float]
    needs_review: bool
    department_correct: bool
    intent_correct: dict[str, bool]
    reasoning: str
    errors: list[str] = field(default_factory=list)


def load_cases(dataset: Path, seed_dir: Path) -> list[Case]:
    seeds = {inc.message_id: inc for inc in SeedSource(seed_dir).fetch()}
    domain = json.loads((seed_dir / "emails.json").read_text(encoding="utf-8"))["domain"]
    cases = []
    for number, line in enumerate(dataset.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("//"):
            continue
        item = json.loads(line)
        if "seed" in item:
            incoming = seeds[f"<{item['seed']}@{domain}>"]
            email = EmailForDecision(
                from_addr=incoming.from_addr,
                subject=incoming.subject,
                body_text=incoming.body_text,
                to_addrs=incoming.to_addrs,
                cc_addrs=incoming.cc_addrs,
                attachments=[
                    _attachment(a.filename, extract_text(a.filename, a.mime, a.content).text)
                    for a in incoming.attachments
                ],
            )
        else:
            email = EmailForDecision(
                from_addr=item["from"],
                subject=item["subject"],
                body_text=item["body"],
                to_addrs=item.get("to", []),
                cc_addrs=item.get("cc", []),
                attachments=[
                    _attachment(a["filename"], a.get("text")) for a in item.get("attachments", [])
                ],
            )
        if not item.get("expected"):
            raise ValueError(f"{dataset.name}:{number}: 'expected' eksik")
        cases.append(
            Case(item["id"], email, item["expected"], frozenset(item.get("acceptable", [])))
        )
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Veri setinde tekrarlanan id var")
    return cases


def _attachment(filename: str, text: str | None) -> AttachmentForDecision:
    return AttachmentForDecision(filename, text, "ok" if text else "unsupported")


def score(case: Case, result: Classification) -> CaseResult:
    predicted = {route.department: route.intent for route in result.routes}
    expected_departments = set(case.expected)
    predicted_departments = set(predicted)
    department_correct = expected_departments <= predicted_departments and (
        predicted_departments <= expected_departments | case.acceptable
    )
    intent_correct = {
        department: predicted.get(department) == intent
        for department, intent in case.expected.items()
        if department != UNKNOWN and department in predicted
    }
    return CaseResult(
        id=case.id,
        expected=case.expected,
        predicted=predicted,
        confidences={route.department: route.confidence for route in result.routes},
        needs_review=result.needs_review,
        department_correct=department_correct,
        intent_correct=intent_correct,
        reasoning=result.reasoning,
        errors=result.errors,
    )


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summarize(results: list[CaseResult]) -> dict[str, Any]:
    auto = [r for r in results if not r.needs_review]
    procurement = [r for r in results if "procurement" in r.intent_correct]
    multi = [r for r in results if len(r.expected) > 1]
    all_intents = [ok for r in results for ok in r.intent_correct.values()]
    return {
        "cases": len(results),
        "department_accuracy": _ratio(sum(r.department_correct for r in results), len(results)),
        "auto_routed": len(auto),
        "auto_routed_error_rate": _ratio(sum(not r.department_correct for r in auto), len(auto)),
        "review_rate": _ratio(len(results) - len(auto), len(results)),
        "review_that_was_correct": sum(r.needs_review and r.department_correct for r in results),
        "procurement_intent": _ratio(
            sum(r.intent_correct["procurement"] for r in procurement), len(procurement)
        ),
        "intent_accuracy_all": _ratio(sum(all_intents), len(all_intents)),
        "multi_department_recall": _ratio(
            sum(len(set(r.expected) & set(r.predicted)) for r in multi),
            sum(len(r.expected) for r in multi),
        ),
        "no_decision": sum(not r.predicted for r in results),
    }


def run(
    cases: Iterable[Case],
    *,
    llm: LLMClient,
    registry: DepartmentRegistry,
    threshold: float,
    progress: Callable[[int, CaseResult], None] | None = None,
) -> list[CaseResult]:
    results = []
    for index, case in enumerate(cases, start=1):
        result = score(case, classify(case.email, llm=llm, registry=registry, threshold=threshold))
        results.append(result)
        if progress:
            progress(index, result)
    return results


def _pct(value: float | None) -> str:
    return "—" if value is None else f"%{value * 100:.1f}"


def render_markdown(
    summary: dict[str, Any], results: list[CaseResult], meta: dict[str, Any]
) -> str:
    def target(key: str, lower_is_better: bool = False) -> str:
        value, goal = summary[key], TARGETS[key]
        if value is None:
            return "—"
        ok = value <= goal if lower_is_better else value >= goal
        return f"{'✅' if ok else '❌'} hedef {'≤' if lower_is_better else '≥'} {_pct(goal)}"

    lines = [
        f"# Yönlendirme değerlendirmesi — {meta['model']}",
        "",
        f"- Tarih: {meta['date']}  ·  Veri seti: `{meta['dataset']}` ({summary['cases']} e-posta)",
        f"- Prompt: `{meta['prompt_version']}`  ·  Güven eşiği: {meta['threshold']}",
        "",
        "| Ölçüt | Değer | Hedef (v1 bölüm 6) |",
        "|---|---|---|",
        f"| 1. Departman doğruluğu | {_pct(summary['department_accuracy'])} | "
        f"{target('department_accuracy')} |",
        f"| 2. Otomatik yönlendirilenlerde hata | {_pct(summary['auto_routed_error_rate'])} "
        f"({summary['auto_routed']} e-posta) | {target('auto_routed_error_rate', True)} |",
        f"| 3. Procurement intent doğruluğu | {_pct(summary['procurement_intent'])} | "
        f"{target('procurement_intent')} |",
        f"| Tüm intent doğruluğu | {_pct(summary['intent_accuracy_all'])} | |",
        f"| Çok departmanlı geri çağırma | {_pct(summary['multi_department_recall'])} | |",
        f"| Manuel incelemeye giden | {_pct(summary['review_rate'])} "
        f"(bunların {summary['review_that_was_correct']} tanesi aslında doğruydu) | |",
        f"| Karar üretilemeyen | {summary['no_decision']} | |",
        "",
        "## Hatalar",
        "",
    ]
    wrong = [r for r in results if not r.department_correct or not all(r.intent_correct.values())]
    if not wrong:
        lines.append("Yok.")
    for r in wrong:
        status = "inceleme" if r.needs_review else "otomatik"
        lines.append(
            f"- **{r.id}** ({status}) beklenen `{r.expected}` → tahmin `{r.predicted}` "
            f"güven `{r.confidences}` — {r.reasoning}"
        )
    return "\n".join(lines) + "\n"


def write_report(
    out_dir: Path, summary: dict[str, Any], results: list[CaseResult], meta: dict[str, Any]
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    slug = meta["model"].replace(":", "-").replace("/", "-")
    path = out_dir / f"routing-{stamp}-{slug}.md"
    path.write_text(render_markdown(summary, results, meta), encoding="utf-8")
    path.with_suffix(".json").write_text(
        json.dumps(
            {"meta": meta, "summary": summary, "results": [asdict(r) for r in results]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path
