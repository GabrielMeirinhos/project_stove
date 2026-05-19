"""Regras de negócio para ``irrigation_event``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import device_repo, irrigation_event_repo
from app.schemas.irrigation_event import (
    IrrigationEvent,
    IrrigationEventCreate,
    IrrigationEventUpdate,
)


def _ensure_device_exists(device_id: UUID) -> None:
    if not device_repo.exists(device_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"device_id {device_id} não existe",
        )


def register_event(data: IrrigationEventCreate) -> IrrigationEvent:
    _ensure_device_exists(data.device_id)
    record = data.model_dump()
    record["trigger_type"] = data.trigger_type.value
    record["id"] = uuid4()
    irrigation_event_repo.add(record)
    return IrrigationEvent(**record)


def get_event(event_id: UUID) -> Optional[IrrigationEvent]:
    record = irrigation_event_repo.get(event_id)
    return IrrigationEvent(**record) if record else None


def list_events(
    *, device_id: Optional[UUID] = None, limit: int = 100, offset: int = 0
) -> List[IrrigationEvent]:
    def predicate(row: dict) -> bool:
        return device_id is None or row["device_id"] == device_id

    rows = irrigation_event_repo.list(
        where=predicate,
        order_by="started_at",
        descending=True,
        limit=limit,
        offset=offset,
    )
    return [IrrigationEvent(**row) for row in rows]


def finalize_event(
    event_id: UUID, data: IrrigationEventUpdate
) -> Optional[IrrigationEvent]:
    """Permite registrar o fim ou o sucesso da irrigação a posteriori."""
    changes = data.model_dump(exclude_unset=True)
    if "finished_at" not in changes:
        changes["finished_at"] = datetime.now(timezone.utc)
    updated = irrigation_event_repo.update(event_id, changes)
    return IrrigationEvent(**updated) if updated else None
