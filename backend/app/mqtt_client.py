"""Cliente MQTT do backend (HiveMQ Cloud).

Conecta no broker no startup do FastAPI, assina os tópicos de telemetria
e heartbeat de todos os ESP32 e roteia cada mensagem para o serviço
correspondente. Também expõe ``publish_pump_command`` para o backend
acionar a bomba remotamente.

Tópicos (convenção GAIA):
* ``gaia/{device_id}/telemetry``  — ESP32 → backend (leituras de sensor)
* ``gaia/{device_id}/heartbeat``  — ESP32 → backend (atualiza last_seen_at)
* ``gaia/{device_id}/cmd/pump``   — backend → ESP32 (acionar bomba)
"""

from __future__ import annotations

import json
import logging
import ssl
from typing import Optional
from uuid import UUID

import paho.mqtt.client as mqtt

from app.config import (
    MQTT_CLIENT_ID,
    MQTT_HOST,
    MQTT_KEEPALIVE,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_TOPIC_PREFIX,
    MQTT_USE_TLS,
    MQTT_USER,
)

logger = logging.getLogger(__name__)

_client: Optional[mqtt.Client] = None


def _on_connect(client: mqtt.Client, userdata, flags, rc, properties=None) -> None:
    if rc == 0:
        logger.info("Conectado ao broker MQTT %s:%s", MQTT_HOST, MQTT_PORT)
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/+/telemetry", qos=1)
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/+/heartbeat", qos=1)
    else:
        logger.error("Falha na conexão MQTT (rc=%s)", rc)


def _on_disconnect(client, userdata, rc, properties=None) -> None:
    logger.warning("MQTT desconectado (rc=%s) — paho tentará reconectar", rc)


def _parse_device_id(topic: str) -> Optional[UUID]:
    """Extrai o ``device_id`` de tópicos no formato ``gaia/{id}/...``."""
    parts = topic.split("/")
    if len(parts) < 3:
        return None
    try:
        return UUID(parts[1])
    except ValueError:
        logger.warning("device_id inválido no tópico %s", topic)
        return None


def _on_message(client, userdata, msg) -> None:
    """Roteia a mensagem MQTT para o serviço correto."""
    # Import tardio: evita ciclo de dependência com app.services no boot.
    from app.schemas.sensor_reading import SensorReadingCreate
    from app.services import device_service, sensor_reading_service

    device_id = _parse_device_id(msg.topic)
    if device_id is None:
        return

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.exception("Payload MQTT inválido em %s", msg.topic)
        return

    try:
        if msg.topic.endswith("/telemetry"):
            data = SensorReadingCreate(device_id=device_id, **payload)
            sensor_reading_service.ingest_reading(data)
        elif msg.topic.endswith("/heartbeat"):
            device_service.heartbeat(device_id)
    except Exception:  # noqa: BLE001 — log e segue; não derruba o loop MQTT
        logger.exception("Erro processando mensagem MQTT em %s", msg.topic)


def start_mqtt() -> Optional[mqtt.Client]:
    """Conecta no broker e inicia o loop em thread separada.

    Retorna ``None`` se as credenciais não foram preenchidas — útil em
    desenvolvimento local quando o broker ainda não está configurado.
    """
    global _client

    if not MQTT_USER or not MQTT_PASSWORD:
        logger.warning(
            "MQTT_USER/MQTT_PASSWORD não preenchidos — cliente MQTT não iniciado."
        )
        return None

    client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    if MQTT_USE_TLS:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)

    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
    client.loop_start()

    _client = client
    return client


def stop_mqtt() -> None:
    global _client
    if _client is not None:
        _client.loop_stop()
        _client.disconnect()
        _client = None


def publish_pump_command(device_id: UUID, action: str, duration_seconds: float) -> bool:
    """Publica um comando de bomba em ``gaia/{device_id}/cmd/pump``.

    Retorna ``True`` se a mensagem entrou na fila de envio do paho.
    """
    if _client is None:
        logger.error("Tentativa de publicar comando sem cliente MQTT ativo")
        return False

    topic = f"{MQTT_TOPIC_PREFIX}/{device_id}/cmd/pump"
    payload = json.dumps({"action": action, "duration_seconds": duration_seconds})
    result = _client.publish(topic, payload, qos=1)
    return result.rc == mqtt.MQTT_ERR_SUCCESS
