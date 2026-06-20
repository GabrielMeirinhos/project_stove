"""Ingestão do tópico MQTT ``planta/status``.

O ESP32 publica leituras periódicas. O payload não traz identificador do
dispositivo (só o nome da planta), então a leitura é salva em
``sensor_reading`` com ``device_id = NULL``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.database import sensor_reading_repo
from app.schemas.sensor_reading import SensorReading, SensorStatus

logger = logging.getLogger(__name__)


def ingest_planta_status(payload: dict) -> SensorReading:
    """Persiste o status recebido como ``sensor_reading``."""
    record = {
        "id": uuid4(),
        "device_id": None,
        "temperature_celsius": payload.get("ar_temp"),
        "humidity_percent": payload.get("ar_umi"),
        "soil_moisture_percent": payload.get("solo_umi"),
        "light_lux": payload.get("luz_bruta"),
        "light_percent": payload.get("luz_pct"),
        "pump_state": payload.get("bomba"),
        "stabilized": payload.get("estabilizado"),
        "firmware_ts": payload.get("ts"),
        "status": SensorStatus.NORMAL.value,
        "recorded_at": datetime.now(timezone.utc),
    }
    sensor_reading_repo.add(record)
    logger.info(
        "planta/status persistido (planta=%s, sensor_reading_id=%s)",
        payload.get("planta"),
        record["id"],
    )
    return SensorReading(**record)
