from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class IncomingAttachment:
    filename: str
    mime: str
    content: bytes


@dataclass(frozen=True)
class IncomingEmail:
    """Bir adaptörün ürettiği, henüz kaydedilmemiş e-posta."""

    from_addr: str
    subject: str
    body_text: str
    message_id: str | None = None
    to_addrs: list[str] = field(default_factory=list)
    cc_addrs: list[str] = field(default_factory=list)
    received_at: datetime | None = None
    attachments: list[IncomingAttachment] = field(default_factory=list)


class EmailSource(Protocol):
    """Giriş adaptörü (ADR-007). Yeni bir kaynak eklemek yeni bir adaptör yazmaktır."""

    name: str

    def fetch(self) -> Iterable[IncomingEmail]: ...
