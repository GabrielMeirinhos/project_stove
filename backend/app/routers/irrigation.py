"""Endpoints REST para ``irrigation_event``."""

from __future__ import annotations

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, get_user_device_ids
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
def register(
    data: IrrigationEventCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> IrrigationEvent:
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(data.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return irrigation_service.register_event(data)


@router.get("", response_model=List[IrrigationEvent], summary="Lista eventos")
def list_all(
    device_id: Optional[UUID] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[IrrigationEvent]:
    events = irrigation_service.list_events(device_id=device_id, limit=limit, offset=offset)
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        events = [e for e in events if str(e.device_id) in allowed]
    return events


@router.get("/{event_id}", response_model=IrrigationEvent, summary="Busca evento por id")
def get(
    event_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> IrrigationEvent:
    event = irrigation_service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="evento não encontrado")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(event.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return event


@router.patch("/{event_id}", response_model=IrrigationEvent,
              summary="Atualiza/finaliza evento")
def update(
    event_id: UUID,
    data: IrrigationEventUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> IrrigationEvent:
    event = irrigation_service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="evento não encontrado")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(event.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return irrigation_service.finalize_event(event_id, data)
