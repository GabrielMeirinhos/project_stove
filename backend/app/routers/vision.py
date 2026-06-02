"""Endpoints REST para ``vision_analysis``."""

from __future__ import annotations

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, get_user_image_ids
from app.schemas.vision_analysis import VisionAnalysis, VisionAnalysisCreate
from app.services import vision_service

router = APIRouter(prefix="/vision-analyses", tags=["vision"])


@router.post(
    "",
    response_model=VisionAnalysis,
    status_code=status.HTTP_201_CREATED,
    summary="Registra análise de visão computacional",
)
def register(
    data: VisionAnalysisCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> VisionAnalysis:
    if current_user["role"] != "superadmin":
        allowed = get_user_image_ids(current_user["user_id"])
        if str(data.image_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return vision_service.register_analysis(data)


@router.get("", response_model=List[VisionAnalysis], summary="Lista análises")
def list_all(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[VisionAnalysis]:
    analyses = vision_service.list_analyses(limit=limit, offset=offset)
    if current_user["role"] != "superadmin":
        allowed = get_user_image_ids(current_user["user_id"])
        analyses = [a for a in analyses if str(a.image_id) in allowed]
    return analyses


@router.get("/{analysis_id}", response_model=VisionAnalysis, summary="Busca análise por id")
def get(
    analysis_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> VisionAnalysis:
    analysis = vision_service.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="análise não encontrada")
    if current_user["role"] != "superadmin":
        allowed = get_user_image_ids(current_user["user_id"])
        if str(analysis.image_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return analysis


@router.get("/by-image/{image_id}", response_model=VisionAnalysis,
            summary="Busca análise por imagem")
def by_image(
    image_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> VisionAnalysis:
    if current_user["role"] != "superadmin":
        allowed = get_user_image_ids(current_user["user_id"])
        if str(image_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    analysis = vision_service.get_analysis_for_image(image_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="análise não encontrada para a imagem")
    return analysis
