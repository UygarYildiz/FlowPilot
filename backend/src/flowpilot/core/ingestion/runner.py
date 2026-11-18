from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from flowpilot.core.ingestion.service import ingest
from flowpilot.core.ingestion.types import EmailSource
from flowpilot.core.storage import AttachmentStorage


@dataclass
class RunReport:
    created: int = 0
    duplicates: int = 0
    failed: list[str] = field(default_factory=list)


def run_source(
    source: EmailSource,
    session_scope: Callable[[], AbstractContextManager[Session]],
    storage: AttachmentStorage,
) -> RunReport:
    """Kaynaktaki her e-postayı ayrı bir işlemde kaydeder; biri bozuksa diğerleri etkilenmez."""
    report = RunReport()
    for incoming in source.fetch():
        try:
            with session_scope() as session:
                result = ingest(session, storage, incoming, source=source.name)
        except Exception as exc:
            report.failed.append(f"{incoming.message_id or incoming.subject}: {exc}")
            continue
        if result.created:
            report.created += 1
        else:
            report.duplicates += 1
    return report
