"""Endpoints REST para ``irrigation_event``."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.irrigation_event import (
    IrrigationEvent,
    IrrigationEventCreate,
    IrrigationEventUpdate,
)
from app.services import irrigation_service

router = APIRouter(prefix="/irrigation-events", tags=["irrigation"])


@router.post(
    "",
    response_model=IrrigationEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um acionamento da bomba de irrigação",
)
def register(data: IrrigationEventCreate) -> IrrigationEvent:
    return irrigation_service.register_event(data)


@router.get("", response_model=List[IrrigationEvent], summary="Lista eventos")
def list_all(
    device_id: Optional[UUID] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[IrrigationEvent]:
    return irrigation_service.list_events(
        device_id=device_id, limit=limit, offset=offset
    )


@router.get(
    "/{event_id}", response_model=IrrigationEvent, summary="Busca evento por id"
)
def get(event_id: UUID) -> IrrigationEvent:
    event = irrigation_service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="evento não encontrado")
    return event


@router.patch(
    "/{event_id}",
    response_model=IrrigationEvent,
    summary="Atualiza/finaliza evento (ex: registrar finished_at)",
)
def update(event_id: UUID, data: IrrigationEventUpdate) -> IrrigationEvent:
    event = irrigation_service.finalize_event(event_id, data)
    if event is None:
        raise HTTPException(status_code=404, detail="evento não encontrado")
    return event
