"""Schemas da entidade ``plant`` (seção 3.1 da documentação)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PlantBase(BaseModel):
    """Campos compartilhados entre criação e resposta."""

    common_name: str = Field(
        ..., max_length=100, description="Nome popular (ex: Alface, Manjericão)"
    )
    scientific_name: Optional[str] = Field(
        None, max_length=150, description="Nome científico (ex: Lactuca sativa)"
    )
    description: Optional[str] = Field(
        None, description="Descrição geral da espécie e características de cultivo"
    )
    optimal_temp_min: float = Field(..., description="Temperatura mínima ideal (°C)")
    optimal_temp_max: float = Field(..., description="Temperatura máxima ideal (°C)")
    optimal_humidity_min: float = Field(
        ..., ge=0, le=100, description="Umidade do ar mínima ideal (%)"
    )
    optimal_humidity_max: float = Field(
        ..., ge=0, le=100, description="Umidade do ar máxima ideal (%)"
    )
    optimal_soil_moisture_min: float = Field(
        ..., ge=0, le=100, description="Umidade mínima do solo ideal (%)"
    )
    optimal_soil_moisture_max: float = Field(
        ..., ge=0, le=100, description="Umidade máxima do solo ideal (%)"
    )
    optimal_light_min: Optional[float] = Field(
        None, ge=0, description="Luminosidade mínima ideal (lux)"
    )
    optimal_light_max: Optional[float] = Field(
        None, ge=0, description="Luminosidade máxima ideal (lux)"
    )
    watering_interval_hours: int = Field(
        ..., gt=0, description="Intervalo recomendado entre irrigações (horas)"
    )

    @model_validator(mode="after")
    def _check_ranges(self) -> "PlantBase":
        if self.optimal_temp_min > self.optimal_temp_max:
            raise ValueError("optimal_temp_min não pode ser maior que optimal_temp_max")
        if self.optimal_humidity_min > self.optimal_humidity_max:
            raise ValueError(
                "optimal_humidity_min não pode ser maior que optimal_humidity_max"
            )
        if self.optimal_soil_moisture_min > self.optimal_soil_moisture_max:
            raise ValueError(
                "optimal_soil_moisture_min não pode ser maior que optimal_soil_moisture_max"
            )
        if (
            self.optimal_light_min is not None
            and self.optimal_light_max is not None
            and self.optimal_light_min > self.optimal_light_max
        ):
            raise ValueError(
                "optimal_light_min não pode ser maior que optimal_light_max"
            )
        return self


class PlantCreate(PlantBase):
    """Payload para cadastro de uma nova espécie."""


class PlantUpdate(BaseModel):
    """Atualização parcial — todos os campos são opcionais."""

    common_name: Optional[str] = Field(None, max_length=100)
    scientific_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    optimal_temp_min: Optional[float] = None
    optimal_temp_max: Optional[float] = None
    optimal_humidity_min: Optional[float] = Field(None, ge=0, le=100)
    optimal_humidity_max: Optional[float] = Field(None, ge=0, le=100)
    optimal_soil_moisture_min: Optional[float] = Field(None, ge=0, le=100)
    optimal_soil_moisture_max: Optional[float] = Field(None, ge=0, le=100)
    optimal_light_min: Optional[float] = Field(None, ge=0)
    optimal_light_max: Optional[float] = Field(None, ge=0)
    watering_interval_hours: Optional[int] = Field(None, gt=0)


class Plant(PlantBase):
    """Representação completa de uma planta persistida."""

    id: UUID
    user_id: Optional[UUID]
    created_at: datetime
