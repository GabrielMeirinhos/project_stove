"""Schemas da entidade ``planta_estufa`` (ciclo de plantação)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PlantaEstufaStart(BaseModel):
    """Payload enviado pela Visão Computacional ao identificar a planta."""

    plant_name: str = Field(
        ..., max_length=100, description="Nome comum da planta identificada"
    )
    life_days: Optional[int] = Field(
        None, gt=0, description="Duração esperada do ciclo de plantação (dias)"
    )


class PlantaEstufa(BaseModel):
    """Registro de uma planta plantada na estufa."""

    id: UUID
    plant_id: UUID
    life_days: Optional[int]
    dia_inclusao: datetime
    dia_saida: Optional[datetime]
    dia_nascenca: Optional[datetime]
