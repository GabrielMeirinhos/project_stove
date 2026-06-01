"""Inicialização da aplicação FastAPI.

Registra todos os routers, configura CORS para o frontend Angular e
gerencia o ciclo de vida do pool de conexões PostgreSQL via
``lifespan``: ao subir o servidor, abre o pool e garante que as tabelas
existem; ao desligar, fecha as conexões.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_current_user
from app.config import API_DESCRIPTION, API_PREFIX, API_TITLE, API_VERSION
from app.db.connection import close_pool, get_pool
from app.db.schema import ensure_admin_user, ensure_schema, ensure_users_table
from app.mqtt_client import start_mqtt, stop_mqtt
from app.routers import (
    alerts,
    auth,
    devices,
    images,
    irrigation,
    plants,
    sensor_readings,
    system_events,
    vision,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001 — assinatura obrigatória
    """Abre o pool, aplica o schema e conecta no broker MQTT no startup."""
    logger.info("Inicializando pool de conexões PostgreSQL...")
    get_pool()
    ensure_schema()
    ensure_users_table()
    ensure_admin_user()
    logger.info("Conectando ao broker MQTT (HiveMQ)...")
    start_mqtt()
    logger.info("Pronto.")
    try:
        yield
    finally:
        logger.info("Encerrando cliente MQTT...")
        stop_mqtt()
        logger.info("Fechando pool de conexões...")
        close_pool()


app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)

# CORS — o dashboard Angular consome esta API a partir de outra origem
# (tipicamente http://localhost:4200 em desenvolvimento). Em produção
# restrinja ``allow_origins`` à origem real do frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix=API_PREFIX)

_protected = (plants, devices, sensor_readings, irrigation, images, vision, system_events, alerts)
for module in _protected:
    app.include_router(
        module.router,
        prefix=API_PREFIX,
        dependencies=[Depends(get_current_user)],
    )


@app.get("/", tags=["health"], summary="Health-check")
def root() -> dict:
    """Endpoint trivial para verificar se o serviço está no ar."""
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "status": "ok",
        "docs": "/docs",
    }
