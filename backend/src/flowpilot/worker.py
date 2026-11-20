"""Sürekli çalışan işleyici (ADR-017): posta kutusunu izler, gelen e-postayı uçtan uca işler.

Her turda: yeni e-postaları içeri al → bekleyenleri sınıflandır → açık rotalarda ajanları çalıştır.
Sonra posta kutusunda yeni e-posta bekler (IDLE; yoksa yoklama). Bekleme süresi dolunca da bir tur
atılır: model geçici olarak erişilemediği için `received` kalan e-postalar böylece yeniden denenir.
Bağlantı koparsa artan aralıklarla yeniden bağlanır.
"""

import imaplib
import logging
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from flowpilot.core.agent_runner import AgentReport, run_pending_agents
from flowpilot.core.decision.engine import Classifier
from flowpilot.core.decision.runner import ClassifyReport, classify_pending
from flowpilot.core.ingestion.runner import RunReport, run_source
from flowpilot.core.ingestion.sources.imap import ImapError, ImapMailbox
from flowpilot.core.models import Email
from flowpilot.core.registry import DepartmentRegistry
from flowpilot.core.storage import AttachmentStorage

log = logging.getLogger("flowpilot.worker")

SessionScope = Callable[[], AbstractContextManager[Session]]


@dataclass
class CycleReport:
    ingest: RunReport
    classify: ClassifyReport
    agents: AgentReport
    seconds: float

    @property
    def did_work(self) -> bool:
        c = self.classify
        return bool(
            self.ingest.created
            or c.routed
            or c.needs_review
            or self.agents.succeeded
            or self.ingest.failed
            or c.failed
            or self.agents.failed
        )


def known_message_ids(session_scope: SessionScope) -> Callable[[str], bool]:
    def is_known(message_id: str) -> bool:
        with session_scope() as session:
            query = select(Email.id).where(Email.message_id == message_id).limit(1)
            return session.scalars(query).first() is not None

    return is_known


def run_cycle(
    mailbox: ImapMailbox,
    *,
    session_scope: SessionScope,
    storage: AttachmentStorage,
    classifier: Classifier,
    registry: DepartmentRegistry,
) -> CycleReport:
    started = time.monotonic()
    ingest = run_source(mailbox, session_scope, storage)
    classify = classify_pending(session_scope, classifier=classifier)
    agents = run_pending_agents(session_scope, registry=registry)
    return CycleReport(ingest, classify, agents, time.monotonic() - started)


def _log_cycle(report: CycleReport) -> None:
    if not report.did_work:
        log.debug("Yeni iş yok")
        return
    c, a = report.classify, report.agents
    log.info(
        "Yeni e-posta: %d · yönlendirildi: %d · insan baksın: %d · ajan: %d (öneri %d) · %.1f sn",
        report.ingest.created,
        c.routed,
        c.needs_review,
        a.succeeded,
        a.proposals,
        report.seconds,
    )
    for line in [*report.ingest.failed, *c.failed, *a.failed]:
        log.warning("  ! %s", line)


def run_worker(
    mailbox: ImapMailbox,
    *,
    session_scope: SessionScope,
    storage: AttachmentStorage,
    classifier: Classifier,
    registry: DepartmentRegistry,
    idle_seconds: float = 300.0,
    poll_seconds: float = 60.0,
    should_stop: Callable[[], bool] = lambda: False,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    backoff = 5.0
    while not should_stop():
        try:
            if not mailbox.is_open:
                mailbox.open()
                mode = "IDLE (anında)" if mailbox.supports_idle else f"yoklama ({poll_seconds:.0f} sn)"
                log.info("Posta kutusuna bağlanıldı · bekleme: %s", mode)
            report = run_cycle(
                mailbox,
                session_scope=session_scope,
                storage=storage,
                classifier=classifier,
                registry=registry,
            )
            _log_cycle(report)
            backoff = 5.0
            if should_stop():
                break
            if mailbox.wait(idle_seconds, poll_seconds=poll_seconds):
                log.info("Yeni e-posta geldi")
        except (ImapError, imaplib.IMAP4.error, OSError) as exc:
            log.warning("Posta kutusu bağlantısı: %s · %.0f sn sonra yeniden denenecek", exc, backoff)
            mailbox.close()
            sleep(backoff)
            backoff = min(backoff * 2, 300.0)
    mailbox.close()
