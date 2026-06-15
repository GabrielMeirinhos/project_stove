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
    """Cria/migra a tabela users (idempotente — seguro para BDs já existentes)."""
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id uuid PRIMARY KEY,
                username varchar(50) NOT NULL UNIQUE,
                hashed_password text NOT NULL,
                is_active boolean NOT NULL DEFAULT TRUE,
                role varchar(20) NOT NULL DEFAULT 'user',
                created_at timestamptz NOT NULL
            );
        """)
        # Migração: adiciona role se a tabela já existia sem ela
        cur.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS role varchar(20) NOT NULL DEFAULT 'user';
        """)
        # Migração: adiciona user_id em plant se ainda não existir
        cur.execute("""
            ALTER TABLE plant ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES users(id);
        """)
        # Migração: cria planta_estufa se schema antigo já tinha sido aplicado
        cur.execute("""
            CREATE TABLE IF NOT EXISTS planta_estufa (
                id uuid PRIMARY KEY,
                plant_id uuid NOT NULL REFERENCES plant(id),
                life_days integer,
                dia_inclusao timestamptz NOT NULL,
                dia_saida timestamptz,
                dia_nascenca timestamptz
            );
        """)
        # Migração: adiciona colunas de luz na plant (catálogo)
        cur.execute("""
            ALTER TABLE plant ADD COLUMN IF NOT EXISTS optimal_light_min numeric;
        """)
        cur.execute("""
            ALTER TABLE plant ADD COLUMN IF NOT EXISTS optimal_light_max numeric;
        """)
        # Migração: renomeia vida_dias -> life_days se a coluna antiga existir
        cur.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'planta_estufa' AND column_name = 'vida_dias'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'planta_estufa' AND column_name = 'life_days'
                ) THEN
                    ALTER TABLE planta_estufa RENAME COLUMN vida_dias TO life_days;
                END IF;
            END $$;
        """)
        # Migração: garante life_days em planta_estufa
        cur.execute("""
            ALTER TABLE planta_estufa ADD COLUMN IF NOT EXISTS life_days integer;
        """)
        # Migração: torna sensor_reading.device_id nullable (planta/status não traz device)
        cur.execute("""
            ALTER TABLE sensor_reading ALTER COLUMN device_id DROP NOT NULL;
        """)
        # Migração: campos vindos do planta/status (luz_pct, bomba, estabilizado, ts)
        cur.execute("""
            ALTER TABLE sensor_reading ADD COLUMN IF NOT EXISTS light_percent numeric;
        """)
        cur.execute("""
            ALTER TABLE sensor_reading ADD COLUMN IF NOT EXISTS pump_state varchar(20);
        """)
        cur.execute("""
            ALTER TABLE sensor_reading ADD COLUMN IF NOT EXISTS stabilized boolean;
        """)
        cur.execute("""
            ALTER TABLE sensor_reading ADD COLUMN IF NOT EXISTS firmware_ts bigint;
        """)
        # Migração: cria planta_alerta se schema antigo não tinha
        cur.execute("""
            CREATE TABLE IF NOT EXISTS planta_alerta (
                id uuid PRIMARY KEY,
                planta varchar(100) NOT NULL,
                tipo varchar(30) NOT NULL,
                nivel varchar(20) NOT NULL,
                mensagem text NOT NULL,
                valor numeric,
                minimo numeric,
                recebido_em timestamptz NOT NULL
            );
        """)


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
            "INSERT INTO users (id, username, hashed_password, is_active, role, created_at) "
            "VALUES (%s, %s, %s, TRUE, 'superadmin', %s)",
            (
                str(uuid.uuid4()),
                config.ADMIN_USERNAME,
                hash_password(config.ADMIN_PASSWORD),
                datetime.now(timezone.utc),
            ),
        )
    logger.info("Usuário admin '%s' criado.", config.ADMIN_USERNAME)