"""Endpoints REST para a entidade ``sensor_reading``."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, get_user_device_ids
from app.schemas.sensor_reading import SensorReading, SensorReadingCreate, SensorStatus
from app.services import sensor_reading_service

router = APIRouter(prefix="/sensor-readings", tags=["sensor_readings"])


@router.post(
    "",
    response_model=SensorReading,
    status_code=status.HTTP_201_CREATED,
    summary="Registra leitura de sensor",
)
def ingest(
    data: SensorReadingCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> SensorReading:
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(data.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return sensor_reading_service.ingest_reading(data)


@router.get("", response_model=List[SensorReading], summary="Consulta histórica")
def list_all(
    device_id: Optional[UUID] = None,
    status_filter: Optional[SensorStatus] = Query(None, alias="status"),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[SensorReading]:
    readings = sensor_reading_service.list_readings(
        device_id=device_id, status_filter=status_filter,
        start=start, end=end, limit=limit, offset=offset,
    )
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        readings = [r for r in readings if str(r.device_id) in allowed]
    return readings


@router.get("/{reading_id}", response_model=SensorReading, summary="Busca leitura por id")
def get(
    reading_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> SensorReading:
    reading = sensor_reading_service.get_reading(reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="leitura não encontrada")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(reading.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return reading
