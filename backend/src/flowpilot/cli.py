"""Komut satırı.

    uv run flowpilot ingest seed | imap        e-postaları içeri al
    uv run flowpilot classify [--limit N]      bekleyen e-postaları Decision Engine'den geçir
    uv run flowpilot eval routing [--limit N]  yönlendirme değerlendirmesi (rapor: evals/results/)
    uv run flowpilot users demo                demo panel kullanıcılarını oluştur/güncelle

Sınıflandırma motoru `FLOWPILOT_DECISION_ENGINE` ile seçilir (llm | clef); llm için sağlayıcı
`FLOWPILOT_LLM_PROVIDER` (fake | gemini).
"""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from flowpilot.bootstrap import get_registry
from flowpilot.config import Settings, get_settings
from flowpilot.core.db import session_scope
from flowpilot.core.decision.runner import classify_pending
from flowpilot.core.ingestion.runner import run_source
from flowpilot.core.ingestion.sources.imap import ImapSource
from flowpilot.core.ingestion.sources.seed import SeedSource
from flowpilot.core.ingestion.types import EmailSource
from flowpilot.core.storage import LocalStorage
from flowpilot.core.users import ensure_demo_users
from flowpilot.decision_setup import build_classifier
from flowpilot.evals import routing

EVALS_DIR = Path("evals")


def _ingest(args: argparse.Namespace, settings: Settings, parser: argparse.ArgumentParser) -> int:
    source: EmailSource
    if args.source == "seed":
        source = SeedSource(args.dir or settings.seed_dir)
    else:
        if not settings.imap_host:
            parser.error("IMAP için FLOWPILOT_IMAP_HOST / _USER / _PASSWORD ayarlanmalı")
        source = ImapSource(
            host=settings.imap_host,
            port=settings.imap_port,
            user=settings.imap_user,
            password=settings.imap_password,
            folder=settings.imap_folder,
            since_days=args.since_days,
        )
    report = run_source(source, session_scope, LocalStorage(settings.storage_dir))
    print(
        f"Yeni: {report.created}  Tekrar (atlandı): {report.duplicates}  Hata: {len(report.failed)}"
    )
    for line in report.failed:
        print(f"  ! {line}")
    return 1 if report.failed else 0


def _classify(args: argparse.Namespace, settings: Settings) -> int:
    classifier = build_classifier(settings, get_registry())
    report = classify_pending(session_scope, classifier=classifier, limit=args.limit)
    print(
        f"Model: {classifier.model_name}  Yönlendirildi: {report.routed}  "
        f"Manuel inceleme: {report.needs_review}  Hata: {len(report.failed)}"
    )
    for line in report.failed:
        print(f"  ! {line}")
    return 1 if report.failed else 0


def _eval_routing(args: argparse.Namespace, settings: Settings) -> int:
    dataset = Path(args.dataset)
    cases = routing.filter_split(routing.load_cases(dataset, Path(settings.seed_dir)), args.split)
    cases = cases[: args.limit]
    classifier = build_classifier(settings, get_registry(), engine=args.engine)

    def progress(index: int, result: routing.CaseResult) -> None:
        mark = "✓" if result.department_correct else "✗"
        review = " (inceleme)" if result.needs_review else ""
        print(f"[{index}/{len(cases)}] {mark} {result.id}: {result.predicted}{review}", flush=True)

    results = routing.run(cases, classifier=classifier, progress=progress)
    summary = routing.summarize(results)
    meta = {
        "model": classifier.model_name,
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset": dataset.as_posix(),
        "prompt_version": classifier.prompt_version,
        "threshold": settings.decision_threshold,
        "split": args.split,
    }
    path = routing.write_report(EVALS_DIR / "results", summary, results, meta)
    print(routing.render_markdown(summary, [], meta).split("## Hatalar")[0])
    print(f"Rapor: {path}")
    return 0


def _users_demo(settings: Settings) -> int:
    with session_scope() as session:
        emails = ensure_demo_users(session, settings.demo_password)
    print("Demo kullanıcıları hazır (şifre: FLOWPILOT_DEMO_PASSWORD):")
    for email in emails:
        print(f"  {email}")
    return 0


def _eval_rescore(args: argparse.Namespace) -> int:
    """Kaydedilmiş raporları yeniden çalıştırmadan bir yarıda puanlar ve yan yana gösterir."""
    keys = [
        ("department_accuracy", "Departman doğruluğu"),
        ("auto_routed_error_rate", "Otomatik yönlendirilenlerde hata"),
        ("procurement_intent", "Procurement intent"),
        ("intent_accuracy_all", "Tüm intent"),
        ("multi_department_recall", "Çok departmanlı geri çağırma"),
        ("review_rate", "Manuel inceleme"),
    ]
    rows = []
    for report in args.reports:
        meta, results = routing.load_results(Path(report))
        subset = routing.filter_split(results, args.split)
        summary = routing.summarize(subset)
        rows.append((f"{meta['model']} ({meta['prompt_version']})", len(subset), summary))
    print(f"| Ölçüt ({args.split}) | " + " | ".join(f"{n} [{c}]" for n, c, _ in rows) + " |")
    print("|---|" + "---|" * len(rows))
    for key, label in keys:
        cells = [routing.percent(s[key]) for _, _, s in rows]
        print(f"| {label} | " + " | ".join(cells) + " |")
    medians = [s.get("median_seconds") for _, _, s in rows]
    print("| Ortanca süre | " + " | ".join(f"{m:.2f} sn" if m else "—" for m in medians) + " |")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Windows konsolunda Türkçe karakterler bozulmasın.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    parser = argparse.ArgumentParser(prog="flowpilot")
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest", help="E-postaları içeri al")
    sources = ingest.add_subparsers(dest="source", required=True)
    seed = sources.add_parser("seed", help="Kurgusal şirketin e-postaları")
    seed.add_argument("--dir", default=None, help="Seed klasörü (varsayılan: ayarlardaki seed_dir)")
    imap = sources.add_parser("imap", help="IMAP posta kutusu (salt-okunur)")
    imap.add_argument("--since-days", type=int, default=7)

    classify = commands.add_parser("classify", help="Bekleyen e-postaları sınıflandır")
    classify.add_argument("--limit", type=int, default=None)

    evaluate = commands.add_parser("eval", help="Değerlendirme çalıştır")
    suites = evaluate.add_subparsers(dest="suite", required=True)
    routing_parser = suites.add_parser("routing", help="Yönlendirme doğruluğu")
    routing_parser.add_argument("--dataset", default=str(EVALS_DIR / "routing" / "dataset.jsonl"))
    routing_parser.add_argument("--limit", type=int, default=None)
    routing_parser.add_argument(
        "--split", choices=["all", "dev", "test"], default="all", help="Geliştirme/test yarısı"
    )
    routing_parser.add_argument(
        "--engine", choices=["llm", "clef"], default=None, help="Varsayılan: ayarlardaki motor"
    )

    rescore = suites.add_parser("rescore", help="Kayıtlı raporları bir yarıda karşılaştır")
    rescore.add_argument("reports", nargs="+", help="evals/results/*.json")
    rescore.add_argument("--split", choices=["all", "dev", "test"], default="test")

    users = commands.add_parser("users", help="Panel kullanıcıları")
    users_commands = users.add_subparsers(dest="users_command", required=True)
    users_commands.add_parser("demo", help="Demo kullanıcılarını oluştur/güncelle")

    args = parser.parse_args(argv)
    settings = get_settings()
    if args.command == "ingest":
        return _ingest(args, settings, parser)
    if args.command == "classify":
        return _classify(args, settings)
    if args.command == "users":
        return _users_demo(settings)
    if args.suite == "rescore":
        return _eval_rescore(args)
    return _eval_routing(args, settings)


if __name__ == "__main__":
    raise SystemExit(main())
