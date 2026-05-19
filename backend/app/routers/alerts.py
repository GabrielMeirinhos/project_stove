"""Endpoints REST para ``alert``."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.alert import Alert, AlertCreate
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=Alert,
    status_code=status.HTTP_201_CREATED,
    summary="Cria alerta manualmente (use /sensor-readings para alertas automáticos)",
)
def create(data: AlertCreate) -> Alert:
    return alert_service.create_alert(data)


@router.get("", response_model=List[Alert], summary="Lista alertas")
def list_all(
    device_id: Optional[UUID] = None,
    only_active: bool = Query(False, description="Inclui apenas alertas não resolvidos"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> List[Alert]:
    return alert_service.list_alerts(
        device_id=device_id, only_active=only_active, limit=limit, offset=offset
    )


@router.get("/{alert_id}", response_model=Alert, summary="Busca alerta por id")
def get(alert_id: UUID) -> Alert:
    alert = alert_service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta não encontrado")
    return alert


@router.post(
    "/{alert_id}/resolve",
    response_model=Alert,
    summary="Marca o alerta como resolvido (preenche resolved_at)",
)
def resolve(alert_id: UUID) -> Alert:
    alert = alert_service.resolve_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta não encontrado")
    return alert
