"""Komut satırı: `uv run flowpilot ingest seed` / `uv run flowpilot ingest imap`."""

import argparse
import sys

from flowpilot.config import get_settings
from flowpilot.core.db import session_scope
from flowpilot.core.ingestion.runner import RunReport, run_source
from flowpilot.core.ingestion.sources.imap import ImapSource
from flowpilot.core.ingestion.sources.seed import SeedSource
from flowpilot.core.ingestion.types import EmailSource
from flowpilot.core.storage import LocalStorage


def _print(report: RunReport) -> None:
    print(
        f"Yeni: {report.created}  Tekrar (atlandı): {report.duplicates}  Hata: {len(report.failed)}"
    )
    for line in report.failed:
        print(f"  ! {line}")


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
    args = parser.parse_args(argv)

    settings = get_settings()
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
    _print(report)
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
