"""Singletons de repositório — um por tabela do schema.

Antes este módulo expunha um repositório em memória (banco "figurativo").
Agora as instâncias apontam para um ``PostgresRepository`` real, mas a
**interface pública é idêntica** (``add``, ``get``, ``list``, ``update``,
``delete``, ``exists``, ``find_one``, ``count``). Por isso os serviços e
routers da aplicação continuam funcionando sem qualquer alteração.

Para reverter ao banco em memória basta substituir cada
``PostgresRepository("...")`` por ``InMemoryRepository("...")``.
"""

from __future__ import annotations

from typing import Any, Dict

from app.db.repository import PostgresRepository

user_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository("users")
plant_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository("plant")
device_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository("device")
sensor_reading_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "sensor_reading"
)
irrigation_event_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "irrigation_event"
)
plant_image_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "plant_image"
)
vision_analysis_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "vision_analysis"
)
system_event_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "system_event"
)
alert_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository("alert")
planta_estufa_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "planta_estufa"
)
planta_alerta_repo: PostgresRepository[Dict[str, Any]] = PostgresRepository(
    "planta_alerta"
)


def reset_database() -> None:
    """Apaga o conteúdo de todas as tabelas (uso em testes).

    A ordem respeita as FKs — primeiro as tabelas dependentes.
    """
    from app.db.connection import get_pool

    statements = (
        "DELETE FROM alert",
        "DELETE FROM planta_alerta",
        "DELETE FROM system_event",
        "DELETE FROM vision_analysis",
        "UPDATE plant_image SET analysis_id = NULL",
        "DELETE FROM plant_image",
        "DELETE FROM irrigation_event",
        "DELETE FROM sensor_reading",
        "DELETE FROM planta_estufa",
        "DELETE FROM device",
        "DELETE FROM plant",
    )
    with get_pool().connection() as conn, conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)
