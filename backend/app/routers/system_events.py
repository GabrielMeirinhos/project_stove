"""Endpoints REST para ``system_event`` (acesso restrito a superadmin)."""

from __future__ import annotations

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_superadmin
from app.schemas.system_event import SystemEvent, SystemEventCreate
from app.services import system_event_service

router = APIRouter(
    prefix="/system-events",
    tags=["system_events"],
    dependencies=[Depends(require_superadmin)],
)


@router.post(
    "",
    response_model=SystemEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Registra evento de auditoria do sistema",
)
def register(data: SystemEventCreate) -> SystemEvent:
    return system_event_service.register_event(data)


@router.get("", response_model=List[SystemEvent], summary="Lista eventos do sistema")
def list_all(
    device_id: Optional[UUID] = None,
    only_unacknowledged: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> List[SystemEvent]:
    return system_event_service.list_events(
        device_id=device_id,
        only_unacknowledged=only_unacknowledged,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=SystemEvent, summary="Busca evento por id")
def get(event_id: UUID) -> SystemEvent:
    event = system_event_service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="evento não encontrado")
    return event


@router.post("/{event_id}/acknowledge", response_model=SystemEvent,
             summary="Marca evento como reconhecido")
def acknowledge(event_id: UUID) -> SystemEvent:
    event = system_event_service.acknowledge(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="evento não encontrado")
    return event
