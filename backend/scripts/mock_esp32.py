"""Mock de ESP32 para teste local do fluxo MQTT.

Publica telemetria simulada no broker HiveMQ no tópico
``gaia/{device_id}/telemetry``. O backend (rodando localmente) deve
estar inscrito no tópico e processar a leitura, calcular o status e
gravar no PostgreSQL (gerando alertas quando necessário).

Uso típico
----------
1. Suba o backend em outro terminal:

    python run.py

2. Bootstrap: cria uma planta + dispositivo e já começa a publicar:

    python scripts/mock_esp32.py --setup --scenario cycle --count 6

3. Já tem um device cadastrado? Use o UUID dele:

    python scripts/mock_esp32.py --device-id <uuid> --scenario warning

Cenários disponíveis
--------------------
* ``normal``    — valores dentro da faixa ideal do tomateiro
* ``warning``   — pouco fora da faixa (gera alerta nível warning)
* ``critical``  — muito fora da faixa (gera alerta nível critical)
* ``cycle``     — alterna entre os três a cada publicação
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Carrega o .env da raiz do projeto
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mock_esp32")


# ---------------------------------------------------------------------------
# Parâmetros do tomateiro (faixa ideal usada pelo backend para classificar)
# ---------------------------------------------------------------------------
TOMATO_PLANT = {
    "common_name": "Tomate (mock)",
    "scientific_name": "Solanum lycopersicum",
    "description": "Planta de teste criada pelo mock_esp32.py",
    "optimal_temp_min": 18.0,
    "optimal_temp_max": 28.0,
    "optimal_humidity_min": 50.0,
    "optimal_humidity_max": 80.0,
    "optimal_soil_moisture_min": 40.0,
    "optimal_soil_moisture_max": 70.0,
    "watering_interval_hours": 12,
}


SCENARIOS = {
    "normal": {
        "temperature_celsius": (22.0, 25.0),
        "humidity_percent": (60.0, 70.0),
        "soil_moisture_percent": (50.0, 65.0),
    },
    "warning": {
        # Pouco fora da faixa — desvio dentro de CRITICAL_DEVIATION (5.0)
        "temperature_celsius": (29.0, 31.0),
        "humidity_percent": (45.0, 48.0),
        "soil_moisture_percent": (35.0, 38.0),
    },
    "critical": {
        # Muito fora da faixa — desvio acima de CRITICAL_DEVIATION
        "temperature_celsius": (35.0, 40.0),
        "humidity_percent": (20.0, 30.0),
        "soil_moisture_percent": (10.0, 20.0),
    },
}


# ---------------------------------------------------------------------------
# REST helpers — usados apenas no modo --setup
# ---------------------------------------------------------------------------
def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.error("HTTP %s em %s: %s", e.code, url, e.read().decode("utf-8"))
        raise


def setup_plant_and_device(api_url: str) -> str:
    """Cria uma planta e um dispositivo via REST e retorna o ``device_id``."""
    logger.info("Criando planta de teste em %s/plants", api_url)
    plant = _post_json(f"{api_url}/plants", TOMATO_PLANT)
    logger.info("Planta criada: id=%s", plant["id"])

    mac = ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))
    device_payload = {
        "plant_id": plant["id"],
        "name": f"ESP32-Mock-{random.randint(100, 999)}",
        "mac_address": mac,
        "firmware_version": "mock-1.0.0",
        "location_description": "Bancada de testes (mock)",
        "is_active": True,
    }
    logger.info("Criando dispositivo em %s/devices", api_url)
    device = _post_json(f"{api_url}/devices", device_payload)
    logger.info("Dispositivo criado: id=%s mac=%s", device["id"], device["mac_address"])
    return device["id"]


# ---------------------------------------------------------------------------
# MQTT publisher
# ---------------------------------------------------------------------------
def _build_payload(scenario: str) -> dict:
    ranges = SCENARIOS[scenario]
    return {
        "temperature_celsius": round(random.uniform(*ranges["temperature_celsius"]), 2),
        "humidity_percent": round(random.uniform(*ranges["humidity_percent"]), 2),
        "soil_moisture_percent": round(
            random.uniform(*ranges["soil_moisture_percent"]), 2
        ),
        "light_lux": round(random.uniform(200.0, 1200.0), 1),
    }


def run(
    *,
    device_id: str,
    scenario: str,
    interval: float,
    count: Optional[int],
    host: str,
    port: int,
    user: str,
    password: str,
    topic_prefix: str,
    use_tls: bool,
) -> None:
    client = mqtt.Client(
        client_id=f"mock-esp32-{random.randint(1000, 9999)}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(user, password)
    if use_tls:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)

    logger.info("Conectando ao broker %s:%s como '%s'...", host, port, user)
    client.connect(host, port, keepalive=60)
    client.loop_start()
    time.sleep(1)  # janela curta para o CONNACK chegar

    telemetry_topic = f"{topic_prefix}/{device_id}/telemetry"
    heartbeat_topic = f"{topic_prefix}/{device_id}/heartbeat"

    cycle_order = ["normal", "warning", "critical"]
    i = 0
    try:
        while count is None or i < count:
            current = (
                cycle_order[i % len(cycle_order)] if scenario == "cycle" else scenario
            )
            payload = _build_payload(current)

            result = client.publish(telemetry_topic, json.dumps(payload), qos=1)
            result.wait_for_publish(timeout=5)
            logger.info("[%s] %s -> %s", current.upper(), telemetry_topic, payload)

            # Um heartbeat a cada 3 publicações
            if i % 3 == 0:
                client.publish(heartbeat_topic, json.dumps({"ts": time.time()}), qos=0)
                logger.info("Heartbeat publicado em %s", heartbeat_topic)

            i += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
    finally:
        client.loop_stop()
        client.disconnect()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Mock de ESP32 publicando MQTT")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/api/v1",
        help="Base URL da API REST (default: http://localhost:8000/api/v1)",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Cria planta + dispositivo via REST antes de começar a publicar",
    )
    parser.add_argument(
        "--device-id",
        help="UUID de um dispositivo já existente (ignorado se --setup for usado)",
    )
    parser.add_argument(
        "--scenario",
        choices=("normal", "warning", "critical", "cycle"),
        default="cycle",
        help="Tipo de leitura a gerar (default: cycle)",
    )
    parser.add_argument(
        "--interval", type=float, default=3.0, help="Intervalo entre publicações (s)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Número de publicações (0 = infinito, default: 10)",
    )
    args = parser.parse_args()

    host = os.getenv("MQTT_HOST")
    port = int(os.getenv("MQTT_PORT", "8883"))
    user = os.getenv("MQTT_USER")
    password = os.getenv("MQTT_PASSWORD")
    use_tls = os.getenv("MQTT_USE_TLS", "true").lower() == "true"
    topic_prefix = os.getenv("MQTT_TOPIC_PREFIX", "gaia")

    if not (host and user and password):
        logger.error(
            "MQTT_HOST/MQTT_USER/MQTT_PASSWORD não estão preenchidos no .env"
        )
        return 1

    if args.setup:
        device_id = setup_plant_and_device(args.api_url)
    elif args.device_id:
        device_id = args.device_id
    else:
        logger.error("Informe --setup ou --device-id <uuid>")
        return 1

    count = None if args.count == 0 else args.count
    run(
        device_id=device_id,
        scenario=args.scenario,
        interval=args.interval,
        count=count,
        host=host,
        port=port,
        user=user,
        password=password,
        topic_prefix=topic_prefix,
        use_tls=use_tls,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
