"""Configurações globais da aplicação.

As credenciais do banco vêm de variáveis de ambiente (e/ou de um arquivo
``.env`` na raiz do projeto, carregado automaticamente via
``python-dotenv``). As variáveis seguem os nomes padrão da libpq
(``PGHOST``, ``PGDATABASE``, etc.) para que a mesma configuração possa
ser reaproveitada por ferramentas como ``psql`` e ``pg_dump``.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega ``.env`` se existir (não sobrescreve variáveis já definidas no
# ambiente — útil em produção, onde o sistema injeta os segredos).
_DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_DOTENV_PATH, override=False)

API_TITLE = "Sistema de Monitoramento de Horta Inteligente"
API_DESCRIPTION = (
    "Backend Python (FastAPI) que implementa o schema descrito na "
    "documentação de banco de dados do projeto integrador. Persistência "
    "em PostgreSQL (Neon)."
)
API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "neondb")
PGUSER = os.getenv("PGUSER", "")
PGPASSWORD = os.getenv("PGPASSWORD", "")
PGSSLMODE = os.getenv("PGSSLMODE", "require")
PGCHANNELBINDING = os.getenv("PGCHANNELBINDING", "require")


def build_conninfo() -> str:
    """Monta a connection string libpq para ``psycopg.connect``."""
    return (
        f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} "
        f"password={PGPASSWORD} sslmode={PGSSLMODE} "
        f"channel_binding={PGCHANNELBINDING}"
    )


# ---------------------------------------------------------------------------
# Thresholds de status do sensor_reading (decisão 6.3 do PDF).
# ---------------------------------------------------------------------------
WARNING_DEVIATION = 0.0
CRITICAL_DEVIATION = 5.0
