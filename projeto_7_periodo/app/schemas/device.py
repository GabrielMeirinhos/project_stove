"""Schemas da entidade ``device`` (seção 3.2 da documentação)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# AA:BB:CC:DD:EE:FF (também aceita formato com hífens)
MAC_ADDRESS_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


class DeviceBase(BaseModel):
    plant_id: UUID = Field(..., description="Planta monitorada por este dispositivo")
    name: str = Field(..., max_length=80, description='Ex: "ESP32-Horta-01"')
    mac_address: str = Field(
        ..., max_length=17, description="MAC físico (AA:BB:CC:DD:EE:FF)"
    )
    firmware_version: Optional[str] = Field(
        None, max_length=20, description="Versão do firmware (ex: 1.2.3)"
    )
    location_description: Optional[str] = Field(
        None, max_length=200, description="Descrição da localização física"
    )
    is_active: bool = Field(True, description="Dispositivo ativo no sistema")

    @field_validator("mac_address")
    @classmethod
    def _validate_mac(cls, value: str) -> str:
        if not MAC_ADDRESS_RE.match(value):
            raise ValueError("mac_address deve estar no formato AA:BB:CC:DD:EE:FF")
        return value.upper().replace("-", ":")


class DeviceCreate(DeviceBase):
    """Payload para registro de um novo ESP32."""


class DeviceUpdate(BaseModel):
    plant_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=80)
    firmware_version: Optional[str] = Field(None, max_length=20)
    location_description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class Device(DeviceBase):
    id: UUID
    last_seen_at: Optional[datetime] = Field(
        None, description="Último heartbeat MQTT recebido"
    )
    created_at: datetime
