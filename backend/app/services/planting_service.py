"""Regras de negócio do ciclo de plantação.

Fluxo (Visão Computacional → Backend → ESP32):
1. Visão Computacional envia o ``plant_name`` identificado e ``vida_dias``.
2. Backend busca a planta cadastrada por ``common_name``.
3. Cria registro em ``planta_estufa`` (dia_inclusao = now).
4. Publica em MQTT ``planta/config`` os dados da planta + vida_dias.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status

from app.database import plant_repo, planta_estufa_repo
from app.mqtt_client import publish_plant_config
from app.schemas.planta_estufa import PlantaEstufa


def start_planting(
    plant_name: str, life_days: Optional[int] = None
) -> PlantaEstufa:
    """Inicia um novo ciclo de plantação a partir do nome identificado."""
    normalized = plant_name.strip().lower()
    plant = plant_repo.find_one(
        lambda r: r["common_name"].strip().lower() == normalized
    )
    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"planta '{plant_name}' não encontrada no catálogo",
        )

    record = {
        "id": uuid4(),
        "plant_id": plant["id"],
        "life_days": life_days,
        "dia_inclusao": datetime.now(timezone.utc),
        "dia_saida": None,
        "dia_nascenca": None,
    }
    planta_estufa_repo.add(record)

    publish_plant_config(
        {
            "nome": plant["common_name"],
            "vida_dias": life_days,
            "solo_min": float(plant["optimal_soil_moisture_min"]),
            "solo_max": float(plant["optimal_soil_moisture_max"]),
            "ar_umi_min": float(plant["optimal_humidity_min"]),
            "ar_umi_max": float(plant["optimal_humidity_max"]),
            "temp_min": float(plant["optimal_temp_min"]),
            "temp_max": float(plant["optimal_temp_max"]),
            "luz_min": (
                float(plant["optimal_light_min"])
                if plant.get("optimal_light_min") is not None
                else None
            ),
            "luz_max": (
                float(plant["optimal_light_max"])
                if plant.get("optimal_light_max") is not None
                else None
            ),
        }
    )

    return PlantaEstufa(**record)
