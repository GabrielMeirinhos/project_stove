"""Endpoints REST do ciclo de plantação."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.planta_estufa import PlantaEstufa, PlantaEstufaStart
from app.services import planting_service

router = APIRouter(prefix="/planting", tags=["planting"])


@router.post(
    "/start",
    response_model=PlantaEstufa,
    status_code=status.HTTP_201_CREATED,
    summary="Inicia um novo ciclo de plantação",
)
def start(data: PlantaEstufaStart) -> PlantaEstufa:
    """Recebe o ``plant_name`` identificado pela Visão Computacional,
    registra o plantio em ``planta_estufa`` e publica MQTT ``planta/config``.
    """
    return planting_service.start_planting(data.plant_name, data.life_days)
