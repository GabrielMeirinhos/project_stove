"""Regras de negócio para ``plant_image``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import device_repo, plant_image_repo
from app.schemas.plant_image import PlantImage, PlantImageCreate, PlantImageUpdate


def _ensure_device_exists(device_id: UUID) -> None:
    if not device_repo.exists(device_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"device_id {device_id} não existe",
        )


def register_image(data: PlantImageCreate) -> PlantImage:
    _ensure_device_exists(data.device_id)
    record = data.model_dump()
    record["image_format"] = data.image_format.value
    record["id"] = uuid4()
    record["analysis_id"] = None
    record["captured_at"] = data.captured_at or datetime.now(timezone.utc)
    plant_image_repo.add(record)
    return PlantImage(**record)


def get_image(image_id: UUID) -> Optional[PlantImage]:
    record = plant_image_repo.get(image_id)
    return PlantImage(**record) if record else None


def list_images(
    *, device_id: Optional[UUID] = None, limit: int = 100, offset: int = 0
) -> List[PlantImage]:
    def predicate(row: dict) -> bool:
        return device_id is None or row["device_id"] == device_id

    rows = plant_image_repo.list(
        where=predicate,
        order_by="captured_at",
        descending=True,
        limit=limit,
        offset=offset,
    )
    return [PlantImage(**row) for row in rows]


def update_image(image_id: UUID, data: PlantImageUpdate) -> Optional[PlantImage]:
    changes = data.model_dump(exclude_unset=True)
    updated = plant_image_repo.update(image_id, changes)
    return PlantImage(**updated) if updated else None
