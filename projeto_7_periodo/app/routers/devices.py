"""Endpoints REST para a entidade ``device``."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.device import Device, DeviceCreate, DeviceUpdate
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo ESP32",
)
def create(data: DeviceCreate) -> Device:
    return device_service.create_device(data)


@router.get("", response_model=List[Device], summary="Lista dispositivos")
def list_all(
    plant_id: Optional[UUID] = None,
    only_active: bool = Query(False, description="Inclui apenas dispositivos ativos"),
) -> List[Device]:
    return device_service.list_devices(plant_id=plant_id, only_active=only_active)


@router.get("/by-mac/{mac_address}", response_model=Device,
            summary="Busca dispositivo pelo MAC")
def get_by_mac(mac_address: str) -> Device:
    device = device_service.get_device_by_mac(mac_address)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return device


@router.get("/{device_id}", response_model=Device, summary="Busca dispositivo por id")
def get(device_id: UUID) -> Device:
    device = device_service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return device


@router.patch("/{device_id}", response_model=Device, summary="Atualiza dispositivo")
def update(device_id: UUID, data: DeviceUpdate) -> Device:
    device = device_service.update_device(device_id, data)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return device


@router.post(
    "/{device_id}/heartbeat",
    response_model=Device,
    summary="Registra heartbeat MQTT (atualiza last_seen_at)",
)
def heartbeat(device_id: UUID) -> Device:
    device = device_service.heartbeat(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return device


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove dispositivo",
)
def delete(device_id: UUID) -> None:
    if not device_service.delete_device(device_id):
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
