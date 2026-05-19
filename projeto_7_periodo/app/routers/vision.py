"""Endpoints REST para ``vision_analysis``."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.vision_analysis import VisionAnalysis, VisionAnalysisCreate
from app.services import vision_service

router = APIRouter(prefix="/vision-analyses", tags=["vision"])


@router.post(
    "",
    response_model=VisionAnalysis,
    status_code=status.HTTP_201_CREATED,
    summary="Registra análise de visão computacional",
)
def register(data: VisionAnalysisCreate) -> VisionAnalysis:
    return vision_service.register_analysis(data)


@router.get("", response_model=List[VisionAnalysis], summary="Lista análises")
def list_all(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[VisionAnalysis]:
    return vision_service.list_analyses(limit=limit, offset=offset)


@router.get(
    "/{analysis_id}", response_model=VisionAnalysis, summary="Busca análise por id"
)
def get(analysis_id: UUID) -> VisionAnalysis:
    analysis = vision_service.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="análise não encontrada")
    return analysis


@router.get(
    "/by-image/{image_id}",
    response_model=VisionAnalysis,
    summary="Busca a análise associada a uma imagem",
)
def by_image(image_id: UUID) -> VisionAnalysis:
    analysis = vision_service.get_analysis_for_image(image_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="análise não encontrada para a imagem")
    return analysis
