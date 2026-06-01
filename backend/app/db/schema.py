"""Bootstrap idempotente do schema do banco.

Na inicialização, verifica se a tabela ``plant`` já existe. Se não,
executa o conteúdo de ``sql/schema.sql`` (mesmo arquivo descrito nas
seções 8 e 9 da documentação). Como o arquivo cria todas as tabelas e
índices em uma única transação, a inicialização é "tudo ou nada".
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
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


def ensure_users_table() -> None:
    """Cria a tabela users se não existir (idempotente — seguro para BDs já existentes)."""
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id uuid PRIMARY KEY,
        username varchar(50) NOT NULL UNIQUE,
        hashed_password text NOT NULL,
        is_active boolean NOT NULL DEFAULT TRUE,
        created_at timestamptz NOT NULL
    );
    """
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(sql)


def ensure_admin_user() -> None:
    """Cria o usuário admin definido em ADMIN_USERNAME/ADMIN_PASSWORD se não existir."""
    from app import config
    from app.auth import hash_password

    if not config.ADMIN_USERNAME or not config.ADMIN_PASSWORD:
        logger.warning("ADMIN_USERNAME ou ADMIN_PASSWORD não definidos — usuário admin não criado.")
        return

    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", (config.ADMIN_USERNAME,))
        if cur.fetchone():
            return
        cur.execute(
            "INSERT INTO users (id, username, hashed_password, is_active, created_at) "
            "VALUES (%s, %s, %s, TRUE, %s)",
            (
                str(uuid.uuid4()),
                config.ADMIN_USERNAME,
                hash_password(config.ADMIN_PASSWORD),
                datetime.now(timezone.utc),
            ),
        )
    logger.info("Usuário admin '%s' criado.", config.ADMIN_USERNAME)