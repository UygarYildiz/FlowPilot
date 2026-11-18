from typing import Any

from sqlalchemy.orm import Session

from flowpilot.core.models import AuditEvent

SYSTEM = "system"


def record(
    session: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: object,
    data: dict[str, Any] | None = None,
) -> AuditEvent:
    """Denetim kaydına bir olay ekler; çağıranın işlemiyle birlikte commit edilir."""
    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        data=data or {},
    )
    session.add(event)
    return event
