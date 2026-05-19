"""Regras de negócio para ``system_event``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import device_repo, system_event_repo
from app.schemas.system_event import (
    SystemEvent,
    SystemEventCreate,
)


def register_event(data: SystemEventCreate) -> SystemEvent:
    if data.device_id is not None and not device_repo.exists(data.device_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"device_id {data.device_id} não existe",
        )

    record = data.model_dump()
    record["severity"] = data.severity.value
    record["id"] = uuid4()
    record["acknowledged"] = False
    record["occurred_at"] = data.occurred_at or datetime.now(timezone.utc)
    system_event_repo.add(record)
    return SystemEvent(**record)


def get_event(event_id: UUID) -> Optional[SystemEvent]:
    record = system_event_repo.get(event_id)
    return SystemEvent(**record) if record else None


def list_events(
    *,
    device_id: Optional[UUID] = None,
    only_unacknowledged: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> List[SystemEvent]:
    def predicate(row: dict) -> bool:
        if device_id is not None and row.get("device_id") != device_id:
            return False
        if only_unacknowledged and row["acknowledged"]:
            return False
        return True

    rows = system_event_repo.list(
        where=predicate,
        order_by="occurred_at",
        descending=True,
        limit=limit,
        offset=offset,
    )
    return [SystemEvent(**row) for row in rows]


def acknowledge(event_id: UUID) -> Optional[SystemEvent]:
    """Marca um evento como reconhecido por um operador."""
    updated = system_event_repo.update(event_id, {"acknowledged": True})
    if updated is None:
        return None
    # ``occurred_at`` permanece imutável por se tratar de log de auditoria
    return SystemEvent(**updated)
