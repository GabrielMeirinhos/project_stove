"""Schemas da entidade ``vision_analysis`` (seção 3.6 da documentação)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Classificação derivada do ``health_score`` (seção 3.6)."""

    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


class VisionAnalysisCreate(BaseModel):
    image_id: UUID = Field(..., description="Imagem que foi analisada")
    model_version: str = Field(
        ..., max_length=30, description="Versão do modelo OpenCV/algoritmo"
    )
    health_score: float = Field(
        ..., ge=0, le=100, description="Índice de saúde (0=crítico, 100=excelente)"
    )
    health_status: HealthStatus
    leaf_coverage_percent: Optional[float] = Field(None, ge=0, le=100)
    detected_issues: Optional[str] = Field(
        None, description="JSON com problemas detectados e coordenadas"
    )
    recommendations: Optional[str] = Field(
        None, description="Sugestões geradas a partir da análise"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confiança da análise (0..1)"
    )
    processing_time_ms: Optional[int] = Field(None, ge=0)
    analyzed_at: Optional[datetime] = None


class VisionAnalysis(BaseModel):
    id: UUID
    image_id: UUID
    model_version: str
    health_score: float
    health_status: HealthStatus
    leaf_coverage_percent: Optional[float]
    detected_issues: Optional[str]
    recommendations: Optional[str]
    confidence_score: float
    processing_time_ms: Optional[int]
    analyzed_at: datetime
