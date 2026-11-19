"""Departman sözleşmesi ve kayıt defteri (ADR-004, v1 kapsamı 3.3).

Çekirdek departmanları yalnızca bu sözleşme üzerinden tanır; departman paketlerini import etmez
(MIMARI.md kural 1). Departmanlar `flowpilot.bootstrap` içinde kayıt defterine eklenir.

Zorunlu: `key/name/description/intents`. İsteğe bağlı (ADR-014): `agent` ve `proposal_types`;
(ADR-015): `tools`. Ajan veriyi değiştirmez; yalnızca öneri döndürür. Öneriyi onaydan sonra
çekirdekteki tek yürütücü (`core/proposals.execute`) `ProposalType.apply` ile uygular. Araçlar
salt-okunurdur: her çağrı geri alınan bir SAVEPOINT içinde çalışır.
"""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel
from sqlalchemy.orm import Session

UNKNOWN = "unknown"


# ---------- Ajan sözleşmesi (ADR-014) ----------


@dataclass(frozen=True)
class AttachmentText:
    filename: str
    text: str | None


class Tools(Protocol):
    """Ajanın kendi departmanının salt-okunur araçlarını çağırdığı arayüz (ADR-015)."""

    def call(self, name: str, **kwargs: Any) -> Any: ...


class NoTools:
    def call(self, name: str, **kwargs: Any) -> Any:
        raise KeyError(f"Araç yok: {name}")


@dataclass(frozen=True)
class Tool:
    """Salt-okunur araç: `fn(session, **kwargs)` düz veri döndürür, ORM nesnesi değil."""

    name: str
    description: str
    fn: Callable[..., Any]


@dataclass(frozen=True)
class AgentContext:
    """Ajanın gördüğü her şey: salt veri ve salt-okunur araçlar; doğrudan veritabanı erişimi yok."""

    email_id: str
    from_addr: str
    to_addrs: tuple[str, ...]
    cc_addrs: tuple[str, ...]
    subject: str
    body_text: str
    attachments: tuple[AttachmentText, ...]
    department: str
    intent: str | None
    priority: str
    tools: Tools = field(default_factory=NoTools)


@dataclass(frozen=True)
class ProposalDraft:
    """Ajanın önerisi: tip, şemaya uyan veri ve panelde gösterilecek kısa özet."""

    type: str
    payload: dict[str, Any]
    summary: str


class Agent(Protocol):
    def handle(self, context: AgentContext) -> list[ProposalDraft]: ...


@dataclass(frozen=True)
class ApplyContext:
    """`apply`'a yürütücünün verdikleri. Oturum, durum değişikliğiyle aynı işlemdedir."""

    session: Session
    proposal_id: str
    idempotency_key: str
    department: str
    email_id: str
    actor: str


ApplyFn = Callable[[ApplyContext, Any], dict[str, Any] | None]


@dataclass(frozen=True)
class ProposalType:
    key: str
    label: str
    schema: type[BaseModel]
    apply: ApplyFn
    requires_approval: bool = True
    description: str = ""


@dataclass(frozen=True)
class Intent:
    key: str
    description: str
    examples: tuple[str, ...] = ()
    label: str = ""  # panelde gösterilen kısa ad; boşsa anahtar gösterilir


@dataclass(frozen=True)
class Department:
    key: str
    name: str
    description: str
    intents: tuple[Intent, ...] = field(default_factory=tuple)
    agent: Agent | None = None
    proposal_types: tuple[ProposalType, ...] = field(default_factory=tuple)
    tools: tuple[Tool, ...] = field(default_factory=tuple)

    def intent_keys(self) -> set[str]:
        return {intent.key for intent in self.intents}

    def proposal_type(self, key: str) -> ProposalType | None:
        return next((p for p in self.proposal_types if p.key == key), None)


class RegistryError(ValueError):
    pass


class DepartmentRegistry:
    def __init__(self, departments: Iterable[Department] = ()) -> None:
        self._departments: dict[str, Department] = {}
        for department in departments:
            self.register(department)

    def register(self, department: Department) -> None:
        if department.key == UNKNOWN:
            raise RegistryError(f"'{UNKNOWN}' ayrılmış bir anahtardır")
        if department.key in self._departments:
            raise RegistryError(f"Departman zaten kayıtlı: {department.key}")
        if not department.intents:
            raise RegistryError(f"Departmanın en az bir intent'i olmalı: {department.key}")
        keys = [intent.key for intent in department.intents]
        if len(keys) != len(set(keys)):
            raise RegistryError(f"Tekrarlanan intent anahtarı: {department.key}")
        if department.agent is not None and not department.proposal_types:
            raise RegistryError(f"Ajanlı departmanın en az bir öneri tipi olmalı: {department.key}")
        type_keys = [p.key for p in department.proposal_types]
        if len(type_keys) != len(set(type_keys)):
            raise RegistryError(f"Tekrarlanan öneri tipi: {department.key}")
        self._departments[department.key] = department

    def unregister(self, key: str) -> None:
        """Departmanı kaldırır (sözleşme sınavı: ekle-kaldır çekirdeğe dokunmadan, kriter 9)."""
        if self._departments.pop(key, None) is None:
            raise RegistryError(f"Departman kayıtlı değil: {key}")

    def get(self, key: str) -> Department | None:
        return self._departments.get(key)

    def keys(self) -> list[str]:
        return list(self._departments)

    def __iter__(self) -> Iterator[Department]:
        return iter(self._departments.values())

    def __len__(self) -> int:
        return len(self._departments)
