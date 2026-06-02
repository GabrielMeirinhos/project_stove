"""Endpoints REST para ``alert``."""

from __future__ import annotations

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, get_user_device_ids
from app.schemas.alert import Alert, AlertCreate
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=Alert,
    status_code=status.HTTP_201_CREATED,
    summary="Cria alerta manualmente",
)
def create(
    data: AlertCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Alert:
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(data.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return alert_service.create_alert(data)


@router.get("", response_model=List[Alert], summary="Lista alertas")
def list_all(
    device_id: Optional[UUID] = None,
    only_active: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[Alert]:
    alerts = alert_service.list_alerts(
        device_id=device_id, only_active=only_active, limit=limit, offset=offset
    )
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        alerts = [a for a in alerts if str(a.device_id) in allowed]
    return alerts


@router.get("/{alert_id}", response_model=Alert, summary="Busca alerta por id")
def get(
    alert_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Alert:
    alert = alert_service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta não encontrado")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(alert.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return alert


@router.post("/{alert_id}/resolve", response_model=Alert, summary="Resolve alerta")
def resolve(
    alert_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Alert:
    alert = alert_service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta não encontrado")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(alert.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return alert_service.resolve_alert(alert_id)
