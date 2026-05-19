"""Regras de negócio para ``sensor_reading``.

Este módulo concentra duas decisões importantes do PDF:

* **Status calculado** (seção 6.3): cada leitura recebe um status
  ``normal``/``warning``/``critical`` no momento da inserção, comparando
  os valores recebidos com os parâmetros ideais da planta vinculada.
* **Alertas automáticos** (seção 3.8): qualquer métrica fora da faixa
  ideal gera um registro em ``alert`` referenciando esta leitura.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status as http_status

from app.config import CRITICAL_DEVIATION
from app.database import (
    alert_repo,
    device_repo,
    plant_repo,
    sensor_reading_repo,
)
from app.schemas.alert import AlertType
from app.schemas.sensor_reading import (
    SensorReading,
    SensorReadingCreate,
    SensorStatus,
)


# ---------------------------------------------------------------------------
# Cálculo de status
# ---------------------------------------------------------------------------
def _classify(value: Optional[float], lo: float, hi: float) -> SensorStatus:
    """Classifica ``value`` em relação ao intervalo ``[lo, hi]``.

    * ``None``  -> ``normal`` (sem leitura, não há como avaliar);
    * dentro da faixa -> ``normal``;
    * fora da faixa por até ``CRITICAL_DEVIATION`` -> ``warning``;
    * desvio acima de ``CRITICAL_DEVIATION`` -> ``critical``.
    """
    if value is None:
        return SensorStatus.NORMAL
    if lo <= value <= hi:
        return SensorStatus.NORMAL
    deviation = (lo - value) if value < lo else (value - hi)
    if deviation > CRITICAL_DEVIATION:
        return SensorStatus.CRITICAL
    return SensorStatus.WARNING


_SEVERITY_ORDER = {
    SensorStatus.NORMAL: 0,
    SensorStatus.WARNING: 1,
    SensorStatus.CRITICAL: 2,
}


def _worst(*statuses: SensorStatus) -> SensorStatus:
    return max(statuses, key=_SEVERITY_ORDER.__getitem__)


def _calculate_status(
    reading: SensorReadingCreate, plant: Dict
) -> Tuple[SensorStatus, List[Tuple[AlertType, str, float, float, float]]]:
    """Devolve o status agregado e a lista de violações por métrica.

    Cada violação retornada é uma tupla
    ``(alert_type, metric_name, threshold, actual, deviation)`` usada
    posteriormente para construir registros em ``alert``.
    """
    violations: List[Tuple[AlertType, str, float, float, float]] = []
    statuses: List[SensorStatus] = []

    checks = (
        (
            reading.temperature_celsius,
            plant["optimal_temp_min"],
            plant["optimal_temp_max"],
            AlertType.TEMPERATURE,
            "temperature_celsius",
        ),
        (
            reading.humidity_percent,
            plant["optimal_humidity_min"],
            plant["optimal_humidity_max"],
            AlertType.HUMIDITY,
            "humidity_percent",
        ),
        (
            reading.soil_moisture_percent,
            plant["optimal_soil_moisture_min"],
            plant["optimal_soil_moisture_max"],
            AlertType.SOIL_MOISTURE,
            "soil_moisture_percent",
        ),
    )

    for value, lo, hi, alert_type, metric_name in checks:
        s = _classify(value, lo, hi)
        statuses.append(s)
        if value is not None and s is not SensorStatus.NORMAL:
            threshold = lo if value < lo else hi
            violations.append((alert_type, metric_name, threshold, value, abs(value - threshold)))

    return _worst(*statuses), violations


# ---------------------------------------------------------------------------
# Geração automática de alertas
# ---------------------------------------------------------------------------
def _build_alert_message(metric: str, threshold: float, actual: float) -> str:
    direction = "abaixo de" if actual < threshold else "acima de"
    return f"Métrica '{metric}' {direction} {threshold} (leitura: {actual})"


def _create_alerts(
    *,
    device_id: UUID,
    sensor_reading_id: UUID,
    violations: List[Tuple[AlertType, str, float, float, float]],
) -> List[Dict]:
    created: List[Dict] = []
    for alert_type, metric, threshold, actual, _deviation in violations:
        record = {
            "id": uuid4(),
            "device_id": device_id,
            "sensor_reading_id": sensor_reading_id,
            "alert_type": alert_type.value,
            "metric_name": metric,
            "threshold_value": float(threshold),
            "actual_value": float(actual),
            "message": _build_alert_message(metric, threshold, actual),
            "resolved": False,
            "triggered_at": datetime.now(timezone.utc),
            "resolved_at": None,
        }
        alert_repo.add(record)
        created.append(record)
    return created


# ---------------------------------------------------------------------------
# API pública do serviço
# ---------------------------------------------------------------------------
def ingest_reading(data: SensorReadingCreate) -> SensorReading:
    """Insere uma leitura, calcula o status e gera alertas se necessário."""
    device = device_repo.get(data.device_id)
    if device is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"device_id {data.device_id} não existe",
        )

    plant = plant_repo.get(device["plant_id"])
    if plant is None:
        # Em teoria a FK garante a integridade; mantemos a checagem
        # explícita para dar uma mensagem clara em modo figurativo.
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="dispositivo aponta para uma planta inexistente",
        )

    aggregated, violations = _calculate_status(data, plant)

    record = {
        "id": uuid4(),
        "device_id": data.device_id,
        "temperature_celsius": data.temperature_celsius,
        "humidity_percent": data.humidity_percent,
        "soil_moisture_percent": data.soil_moisture_percent,
        "light_lux": data.light_lux,
        "status": aggregated.value,
        "recorded_at": data.recorded_at or datetime.now(timezone.utc),
    }
    sensor_reading_repo.add(record)

    # Atualiza o último heartbeat do dispositivo (uma leitura também
    # comprova que o ESP32 está online).
    device_repo.update(device["id"], {"last_seen_at": record["recorded_at"]})

    if violations:
        _create_alerts(
            device_id=data.device_id,
            sensor_reading_id=record["id"],
            violations=violations,
        )

    return SensorReading(**record)


def get_reading(reading_id: UUID) -> Optional[SensorReading]:
    record = sensor_reading_repo.get(reading_id)
    return SensorReading(**record) if record else None


def list_readings(
    *,
    device_id: Optional[UUID] = None,
    status_filter: Optional[SensorStatus] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[SensorReading]:
    """Lista leituras com filtros típicos do dashboard.

    Os índices ``(device_id, recorded_at DESC)`` da seção 5 do PDF
    suportam exatamente esse padrão de consulta.
    """

    def predicate(row: dict) -> bool:
        if device_id is not None and row["device_id"] != device_id:
            return False
        if status_filter is not None and row["status"] != status_filter.value:
            return False
        if start is not None and row["recorded_at"] < start:
            return False
        if end is not None and row["recorded_at"] > end:
            return False
        return True

    rows = sensor_reading_repo.list(
        where=predicate,
        order_by="recorded_at",
        descending=True,
        limit=limit,
        offset=offset,
    )
    return [SensorReading(**row) for row in rows]
