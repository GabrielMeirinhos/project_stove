"""Schemas da entidade ``alert`` (seção 3.8 da documentação)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlertType(str, Enum):
    """Categorias previstas no PDF (seção 3.8)."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SOIL_MOISTURE = "soil_moisture"
    CONNECTIVITY = "connectivity"


class AlertCreate(BaseModel):
    """Geralmente os alertas são gerados automaticamente pelo backend
    (a partir de um ``sensor_reading``), mas o cliente também pode
    criar alertas manualmente — por exemplo, alertas de conectividade.
    """

    device_id: UUID
    sensor_reading_id: Optional[UUID] = None
    alert_type: AlertType
    metric_name: str = Field(..., max_length=50)
    threshold_value: float
    actual_value: float
    message: str = Field(..., max_length=300)


class AlertResolve(BaseModel):
    """Payload para marcar um alerta como resolvido."""

    resolved: bool = True


class Alert(BaseModel):
    id: UUID
    device_id: UUID
    sensor_reading_id: Optional[UUID]
    alert_type: AlertType
    metric_name: str
    threshold_value: float
    actual_value: float
    message: str
    resolved: bool
    triggered_at: datetime
    resolved_at: Optional[datetime]
