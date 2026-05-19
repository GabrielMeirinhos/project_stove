"""Regras de negócio para a entidade ``plant``."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from app.database import plant_repo
from app.schemas.plant import Plant, PlantCreate, PlantUpdate


def create_plant(data: PlantCreate) -> Plant:
    """Persiste uma nova planta e devolve sua representação."""
    record = data.model_dump()
    record.update(
        {
            "id": uuid4(),
            "created_at": datetime.now(timezone.utc),
        }
    )
    plant_repo.add(record)
    return Plant(**record)


def get_plant(plant_id: UUID) -> Optional[Plant]:
    record = plant_repo.get(plant_id)
    return Plant(**record) if record else None


def list_plants(limit: int = 100, offset: int = 0) -> List[Plant]:
    rows = plant_repo.list(order_by="created_at", descending=True,
                           limit=limit, offset=offset)
    return [Plant(**row) for row in rows]


def update_plant(plant_id: UUID, data: PlantUpdate) -> Optional[Plant]:
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        return get_plant(plant_id)
    updated = plant_repo.update(plant_id, changes)
    return Plant(**updated) if updated else None


def delete_plant(plant_id: UUID) -> bool:
    return plant_repo.delete(plant_id)
