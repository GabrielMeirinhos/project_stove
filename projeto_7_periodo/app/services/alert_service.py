"""Regras de negócio para ``alert``.

A maior parte dos alertas é criada automaticamente pelo
``sensor_reading_service`` quando uma leitura sai da faixa ideal. Este
módulo expõe os endpoints de **listagem** e **resolução** de alertas
usados pelo frontend Angular para exibir o painel de alertas ativos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.database import alert_repo, device_repo
from app.schemas.alert import Alert, AlertCreate


def create_alert(data: AlertCreate) -> Alert:
    if not device_repo.exists(data.device_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"device_id {data.device_id} não existe",
        )
    record = data.model_dump()
    record["alert_type"] = data.alert_type.value
    record.update(
        {
            "id": uuid4(),
            "resolved": False,
            "triggered_at": datetime.now(timezone.utc),
            "resolved_at": None,
        }
    )
    alert_repo.add(record)
    return Alert(**record)


def get_alert(alert_id: UUID) -> Optional[Alert]:
    record = alert_repo.get(alert_id)
    return Alert(**record) if record else None


def list_alerts(
    *,
    device_id: Optional[UUID] = None,
    only_active: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> List[Alert]:
    def predicate(row: dict) -> bool:
        if device_id is not None and row["device_id"] != device_id:
            return False
        if only_active and row["resolved"]:
            return False
        return True

    rows = alert_repo.list(
        where=predicate,
        order_by="triggered_at",
        descending=True,
        limit=limit,
        offset=offset,
    )
    return [Alert(**row) for row in rows]


def resolve_alert(alert_id: UUID) -> Optional[Alert]:
    record = alert_repo.get(alert_id)
    if record is None:
        return None
    if record["resolved"]:
        return Alert(**record)
    updated = alert_repo.update(
        alert_id,
        {
            "resolved": True,
            "resolved_at": datetime.now(timezone.utc),
        },
    )
    return Alert(**updated) if updated else None
