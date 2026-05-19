"""Pool de conexões PostgreSQL.

A aplicação usa um único ``psycopg_pool.ConnectionPool`` compartilhado
entre os request handlers do FastAPI. O pool é aberto no ``lifespan``
de ``app.main`` e fechado no shutdown.

Cada conexão obtida do pool já vem com ``row_factory=dict_row``, de modo
que ``cur.fetchone()`` / ``cur.fetchall()`` retornam dicionários — o
mesmo formato esperado pelos serviços (que tratavam os registros do
banco figurativo como ``Dict[str, Any]``).
"""

from __future__ import annotations

from typing import Optional

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import build_conninfo

_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    """Retorna o pool global, inicializando-o sob demanda."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=build_conninfo(),
            min_size=1,
            max_size=8,
            kwargs={"row_factory": dict_row, "autocommit": True},
            open=False,
        )
        _pool.open()
        _pool.wait()
    return _pool


def close_pool() -> None:
    """Fecha o pool ao desligar a aplicação."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None