"""Schemas da entidade ``sensor_reading`` (seção 3.3 da documentação).

A coluna ``status`` é **calculada pelo backend** no momento da inserção
(decisão de design 6.3 do PDF). Por isso ela aparece apenas no schema de
resposta — o cliente nunca a envia.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SensorStatus(str, Enum):
    """Classificação calculada de uma leitura.

    Definida na seção 3.3 do PDF: ``normal``, ``warning`` ou ``critical``.
    """

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class SensorReadingCreate(BaseModel):
    """Leitura recebida via MQTT/HTTP a partir de um ESP32."""

    device_id: UUID = Field(..., description="Dispositivo que realizou a leitura")
    temperature_celsius: Optional[float] = Field(None, description="Temperatura (°C)")
    humidity_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Umidade do ar (%)"
    )
    soil_moisture_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Umidade do solo (%)"
    )
    light_lux: Optional[float] = Field(
        None, ge=0, description="Luminosidade ambiente (lux)"
    )
    recorded_at: Optional[datetime] = Field(
        None,
        description=(
            "Timestamp da coleta no sensor. Quando ausente, o backend "
            "preenche com o instante atual."
        ),
    )


class SensorReading(BaseModel):
    """Leitura persistida com ``status`` já calculado."""

    id: UUID
    device_id: UUID
    temperature_celsius: Optional[float]
    humidity_percent: Optional[float]
    soil_moisture_percent: Optional[float]
    light_lux: Optional[float]
    status: SensorStatus
    recorded_at: datetime
