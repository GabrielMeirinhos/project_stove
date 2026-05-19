"""Endpoints REST para a entidade ``plant``."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.plant import Plant, PlantCreate, PlantUpdate
from app.services import plant_service

router = APIRouter(prefix="/plants", tags=["plants"])


@router.post(
    "",
    response_model=Plant,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma nova espécie de planta",
)
def create(data: PlantCreate) -> Plant:
    return plant_service.create_plant(data)


@router.get("", response_model=List[Plant], summary="Lista plantas cadastradas")
def list_all(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[Plant]:
    return plant_service.list_plants(limit=limit, offset=offset)


@router.get("/{plant_id}", response_model=Plant, summary="Busca planta por id")
def get(plant_id: UUID) -> Plant:
    plant = plant_service.get_plant(plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="planta não encontrada")
    return plant


@router.patch("/{plant_id}", response_model=Plant, summary="Atualiza planta")
def update(plant_id: UUID, data: PlantUpdate) -> Plant:
    plant = plant_service.update_plant(plant_id, data)
    if plant is None:
        raise HTTPException(status_code=404, detail="planta não encontrada")
    return plant


@router.delete(
    "/{plant_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove planta",
)
def delete(plant_id: UUID) -> None:
    if not plant_service.delete_plant(plant_id):
        raise HTTPException(status_code=404, detail="planta não encontrada")
