"""Ingestão do tópico MQTT ``planta/alerta``.

O ESP32 publica um payload com o nome da planta e uma lista de alertas.
Cada item do array vira uma linha em ``planta_alerta``. Não há vínculo
com ``device`` nem ``planta_estufa`` (o payload não traz identificador
único do ESP).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from app.database import planta_alerta_repo
from app.schemas.planta_alerta import PlantaAlerta, PlantaAlertaPayload

logger = logging.getLogger(__name__)


def ingest_planta_alerta(payload: dict) -> List[PlantaAlerta]:
    """Valida o payload e persiste cada alerta do array."""
    data = PlantaAlertaPayload(**payload)
    now = datetime.now(timezone.utc)
    persisted: List[PlantaAlerta] = []

    for item in data.alertas:
        record = {
            "id": uuid4(),
            "planta": data.planta,
            "tipo": item.tipo,
            "nivel": item.nivel,
            "mensagem": item.mensagem,
            "valor": item.valor,
            "minimo": item.minimo,
            "recebido_em": now,
        }
        planta_alerta_repo.add(record)
        persisted.append(PlantaAlerta(**record))

    logger.info(
        "planta/alerta persistido (planta=%s, qtd=%d)", data.planta, len(persisted)
    )
    return persisted
