"""Schemas da entidade ``system_event`` (seção 3.7 da documentação)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemEventCreate(BaseModel):
    device_id: Optional[UUID] = Field(
        None,
        description="Dispositivo relacionado (nulo para eventos globais)",
    )
    event_type: str = Field(
        ...,
        max_length=50,
        description='Ex: "device_connected", "sensor_failure", "firmware_update"',
    )
    severity: EventSeverity
    description: str = Field(..., max_length=500)
    payload_json: Optional[str] = Field(
        None, description="Metadados em JSON livre (decisão 6.4 do PDF)"
    )
    occurred_at: Optional[datetime] = None


class SystemEventAcknowledge(BaseModel):
    """Marca um evento como reconhecido por um operador."""

    acknowledged: bool = True


class SystemEvent(BaseModel):
    id: UUID
    device_id: Optional[UUID]
    event_type: str
    severity: EventSeverity
    description: str
    payload_json: Optional[str]
    acknowledged: bool
    occurred_at: datetime
