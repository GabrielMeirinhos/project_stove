"""Schemas da entidade ``irrigation_event`` (seção 3.4 da documentação)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    """Origem do acionamento da bomba (seção 3.4 do PDF)."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"


class IrrigationEventCreate(BaseModel):
    device_id: UUID
    trigger_type: TriggerType
    duration_seconds: float = Field(..., gt=0, description="Duração total (s)")
    water_volume_ml: Optional[float] = Field(
        None, ge=0, description="Volume estimado de água utilizado (ml)"
    )
    trigger_reason: Optional[str] = Field(
        None,
        max_length=300,
        description='Motivo legível (ex: "Solo abaixo de 30%")',
    )
    success: bool = Field(True, description="Irrigação concluída com sucesso?")
    started_at: datetime = Field(..., description="Início da irrigação")
    finished_at: Optional[datetime] = Field(None, description="Fim da irrigação")


class IrrigationEventUpdate(BaseModel):
    """Permite, por exemplo, registrar o ``finished_at`` posteriormente."""

    water_volume_ml: Optional[float] = Field(None, ge=0)
    trigger_reason: Optional[str] = Field(None, max_length=300)
    success: Optional[bool] = None
    finished_at: Optional[datetime] = None


class IrrigationEvent(BaseModel):
    id: UUID
    device_id: UUID
    trigger_type: TriggerType
    duration_seconds: float
    water_volume_ml: Optional[float]
    trigger_reason: Optional[str]
    success: bool
    started_at: datetime
    finished_at: Optional[datetime]
