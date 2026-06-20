"""Schemas da entidade ``planta_alerta`` (ciclo de rotina).

Espelha o payload publicado pelo ESP32 no tópico MQTT ``planta/alerta``.
Não há vínculo com ``device`` nem ``planta_estufa`` ainda: o payload do
firmware só traz o nome da planta. A coluna ``planta_estufa_id`` pode
ser adicionada quando o ESP passar a publicar um identificador único.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PlantaAlertaItem(BaseModel):
    """Um alerta individual dentro do array ``alertas`` do payload."""

    tipo: str = Field(..., max_length=30, description="solo, ar_umi, ar_temp, luz, ...")
    nivel: str = Field(..., max_length=20, description="critico, alerta, ...")
    mensagem: str
    valor: Optional[float] = None
    minimo: Optional[float] = None


class PlantaAlertaPayload(BaseModel):
    """Payload completo recebido no tópico ``planta/alerta``."""

    planta: str = Field(..., max_length=100)
    alertas: List[PlantaAlertaItem]


class PlantaAlerta(BaseModel):
    """Registro persistido — uma linha por alerta do array."""

    id: UUID
    planta: str
    tipo: str
    nivel: str
    mensagem: str
    valor: Optional[float]
    minimo: Optional[float]
    recebido_em: datetime
