"""Regras de negócio para a entidade ``device``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import device_repo, plant_repo
from app.schemas.device import Device, DeviceCreate, DeviceUpdate


def _ensure_plant_exists(plant_id: UUID) -> None:
    if not plant_repo.exists(plant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"plant_id {plant_id} não existe",
        )


def create_device(data: DeviceCreate) -> Device:
    _ensure_plant_exists(data.plant_id)

    if device_repo.find_one(lambda r: r["mac_address"] == data.mac_address):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"mac_address {data.mac_address} já cadastrado",
        )

    record = data.model_dump()
    record.update(
        {
            "id": uuid4(),
            "last_seen_at": None,
            "created_at": datetime.now(timezone.utc),
        }
    )
    device_repo.add(record)
    return Device(**record)


def get_device(device_id: UUID) -> Optional[Device]:
    record = device_repo.get(device_id)
    return Device(**record) if record else None


def get_device_by_mac(mac_address: str) -> Optional[Device]:
    record = device_repo.find_one(lambda r: r["mac_address"] == mac_address.upper())
    return Device(**record) if record else None


def list_devices(
    *, plant_id: Optional[UUID] = None, only_active: bool = False
) -> List[Device]:
    def predicate(row: dict) -> bool:
        if plant_id is not None and row["plant_id"] != plant_id:
            return False
        if only_active and not row["is_active"]:
            return False
        return True

    rows = device_repo.list(where=predicate, order_by="created_at", descending=True)
    return [Device(**row) for row in rows]


def update_device(device_id: UUID, data: DeviceUpdate) -> Optional[Device]:
    changes = data.model_dump(exclude_unset=True)
    if "plant_id" in changes:
        _ensure_plant_exists(changes["plant_id"])
    updated = device_repo.update(device_id, changes)
    return Device(**updated) if updated else None


def delete_device(device_id: UUID) -> bool:
    return device_repo.delete(device_id)


def heartbeat(device_id: UUID) -> Optional[Device]:
    """Atualiza ``last_seen_at`` simulando um heartbeat MQTT (seção 3.2)."""
    updated = device_repo.update(
        device_id, {"last_seen_at": datetime.now(timezone.utc)}
    )
    return Device(**updated) if updated else None
