"""Bootstrap idempotente do schema do banco.

Na inicialização, verifica se a tabela ``plant`` já existe. Se não,
executa o conteúdo de ``sql/schema.sql`` (mesmo arquivo descrito nas
seções 8 e 9 da documentação). Como o arquivo cria todas as tabelas e
índices em uma única transação, a inicialização é "tudo ou nada".
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.db.connection import get_pool

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "SQL" / "schema.sql"


def _plant_table_exists() -> bool:
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.plant') AS oid")
        row = cur.fetchone()
        return bool(row and row["oid"])


def ensure_schema() -> None:
    """Cria as tabelas se ainda não existirem."""
    if _plant_table_exists():
        logger.info("Schema já presente — pulando bootstrap.")
        return

    logger.info("Tabelas ausentes; aplicando %s ...", _SCHEMA_PATH)
    sql_text = _SCHEMA_PATH.read_text(encoding="utf-8")

    with get_pool().connection() as conn:
        # Executa todo o script numa única transação (autocommit=True no
        # pool — para o bootstrap explicitamente abrimos um bloco).
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                cur.execute(sql_text)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.autocommit = True
    logger.info("Schema aplicado com sucesso.")