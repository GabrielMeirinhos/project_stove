"""Endpoints REST para ``plant_image``."""

from __future__ import annotations

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, get_user_device_ids
from app.schemas.plant_image import PlantImage, PlantImageCreate, PlantImageUpdate
from app.services import image_service

router = APIRouter(prefix="/images", tags=["images"])


@router.post(
    "",
    response_model=PlantImage,
    status_code=status.HTTP_201_CREATED,
    summary="Registra imagem capturada pela câmera",
)
def register(
    data: PlantImageCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> PlantImage:
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(data.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return image_service.register_image(data)


@router.get("", response_model=List[PlantImage], summary="Lista imagens")
def list_all(
    device_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[PlantImage]:
    images = image_service.list_images(device_id=device_id, limit=limit, offset=offset)
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        images = [img for img in images if str(img.device_id) in allowed]
    return images


@router.get("/{image_id}", response_model=PlantImage, summary="Busca imagem por id")
def get(
    image_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> PlantImage:
    image = image_service.get_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="imagem não encontrada")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(image.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return image


@router.patch("/{image_id}", response_model=PlantImage, summary="Atualiza imagem")
def update(
    image_id: UUID,
    data: PlantImageUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> PlantImage:
    image = image_service.get_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="imagem não encontrada")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(image.device_id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return image_service.update_image(image_id, data)
