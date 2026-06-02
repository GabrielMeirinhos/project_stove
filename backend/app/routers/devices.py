"""Endpoints REST para a entidade ``device``."""

from __future__ import annotations

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, get_user_device_ids, require_superadmin
from app.schemas.device import Device, DeviceCreate, DeviceUpdate
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo ESP32 (superadmin only)",
    dependencies=[Depends(require_superadmin)],
)
def create(data: DeviceCreate) -> Device:
    return device_service.create_device(data)


@router.get("", response_model=List[Device], summary="Lista dispositivos")
def list_all(
    plant_id: Optional[UUID] = None,
    only_active: bool = Query(False),
    current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> List[Device]:
    devices = device_service.list_devices(plant_id=plant_id, only_active=only_active)
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        devices = [d for d in devices if str(d.id) in allowed]
    return devices


@router.get("/by-mac/{mac_address}", response_model=Device,
            summary="Busca dispositivo pelo MAC")
def get_by_mac(
    mac_address: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Device:
    device = device_service.get_device_by_mac(mac_address)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(device.id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return device


@router.get("/{device_id}", response_model=Device, summary="Busca dispositivo por id")
def get(
    device_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Device:
    device = device_service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    if current_user["role"] != "superadmin":
        allowed = get_user_device_ids(current_user["user_id"])
        if str(device.id) not in allowed:
            raise HTTPException(status_code=403, detail="Acesso negado")
    return device


@router.patch(
    "/{device_id}",
    response_model=Device,
    summary="Atualiza dispositivo (superadmin only)",
    dependencies=[Depends(require_superadmin)],
)
def update(device_id: UUID, data: DeviceUpdate) -> Device:
    device = device_service.update_device(device_id, data)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return device


@router.post(
    "/{device_id}/heartbeat",
    response_model=Device,
    summary="Registra heartbeat MQTT",
)
def heartbeat(device_id: UUID) -> Device:
    device = device_service.heartbeat(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return device


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove dispositivo (superadmin only)",
    dependencies=[Depends(require_superadmin)],
)
def delete(device_id: UUID) -> None:
    if not device_service.delete_device(device_id):
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
