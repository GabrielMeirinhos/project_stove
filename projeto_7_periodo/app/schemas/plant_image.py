"""Schemas da entidade ``plant_image`` (seção 3.5 da documentação)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ImageFormat(str, Enum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"


class PlantImageCreate(BaseModel):
    device_id: UUID = Field(..., description="Dispositivo/câmera que capturou")
    image_base64: Optional[str] = Field(
        None, description="Conteúdo codificado em Base64 (modo acadêmico)"
    )
    image_format: ImageFormat = Field(..., description="Formato da imagem")
    width_px: Optional[int] = Field(None, gt=0)
    height_px: Optional[int] = Field(None, gt=0)
    file_size_bytes: Optional[int] = Field(None, gt=0)
    storage_path: Optional[str] = Field(
        None,
        max_length=500,
        description=(
            "Caminho em disco ou URL externa. Recomendado em produção em "
            "vez de armazenar o conteúdo em ``image_base64`` (seção 6.2)."
        ),
    )
    captured_at: Optional[datetime] = None


class PlantImageUpdate(BaseModel):
    """Tipicamente usado para vincular a imagem à análise de visão."""

    analysis_id: Optional[UUID] = None
    storage_path: Optional[str] = Field(None, max_length=500)


class PlantImage(BaseModel):
    id: UUID
    device_id: UUID
    analysis_id: Optional[UUID]
    image_base64: Optional[str]
    image_format: ImageFormat
    width_px: Optional[int]
    height_px: Optional[int]
    file_size_bytes: Optional[int]
    storage_path: Optional[str]
    captured_at: datetime
