"""Endpoints REST para a entidade ``plant``."""

from __future__ import annotations

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, require_superadmin
from app.schemas.plant import Plant, PlantCreate, PlantUpdate
from app.services import plant_service

router = APIRouter(prefix="/plants", tags=["plants"])


@router.post(
    "",
    response_model=Plant,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma nova planta",
)
def create(
    data: PlantCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Plant:
    user_id = UUID(current_user["user_id"]) if current_user["role"] != "superadmin" else None
    return plant_service.create_plant(data, user_id=user_id)


@router.get("", response_model=List[Plant], summary="Lista plantas cadastradas")
def list_all(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[Plant]:
    user_id = None if current_user["role"] == "superadmin" else UUID(current_user["user_id"])
    return plant_service.list_plants(limit=limit, offset=offset, user_id=user_id)


@router.get("/{plant_id}", response_model=Plant, summary="Busca planta por id")
def get(
    plant_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Plant:
    plant = plant_service.get_plant(plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="planta não encontrada")
    if current_user["role"] != "superadmin" and str(plant.user_id) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return plant


@router.patch("/{plant_id}", response_model=Plant, summary="Atualiza planta")
def update(
    plant_id: UUID,
    data: PlantUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Plant:
    plant = plant_service.get_plant(plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="planta não encontrada")
    if current_user["role"] != "superadmin" and str(plant.user_id) != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    updated = plant_service.update_plant(plant_id, data)
    return updated


@router.delete(
    "/{plant_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove planta",
    dependencies=[Depends(require_superadmin)],
)
def delete(plant_id: UUID) -> None:
    if not plant_service.delete_plant(plant_id):
        raise HTTPException(status_code=404, detail="planta não encontrada")
