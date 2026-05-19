"""Endpoints REST para a entidade ``sensor_reading``."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.sensor_reading import (
    SensorReading,
    SensorReadingCreate,
    SensorStatus,
)
from app.services import sensor_reading_service

router = APIRouter(prefix="/sensor-readings", tags=["sensor_readings"])


@router.post(
    "",
    response_model=SensorReading,
    status_code=status.HTTP_201_CREATED,
    summary="Registra leitura de sensor (calcula status e gera alertas)",
)
def ingest(data: SensorReadingCreate) -> SensorReading:
    """Endpoint que normalmente é alimentado pelo Spring Boot (ou pelo
    ESP32 diretamente, em uma evolução futura). O backend calcula o
    status da leitura e gera registros em ``alert`` para qualquer métrica
    fora da faixa ideal da planta vinculada.
    """
    return sensor_reading_service.ingest_reading(data)


@router.get("", response_model=List[SensorReading], summary="Consulta histórica")
def list_all(
    device_id: Optional[UUID] = None,
    status_filter: Optional[SensorStatus] = Query(None, alias="status"),
    start: Optional[datetime] = Query(None, description="Início do intervalo"),
    end: Optional[datetime] = Query(None, description="Fim do intervalo"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> List[SensorReading]:
    return sensor_reading_service.list_readings(
        device_id=device_id,
        status_filter=status_filter,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{reading_id}", response_model=SensorReading, summary="Busca leitura por id"
)
def get(reading_id: UUID) -> SensorReading:
    reading = sensor_reading_service.get_reading(reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="leitura não encontrada")
    return reading
