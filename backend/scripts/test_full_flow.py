"""Teste end-to-end dos ciclos de plantação e rotina (in-process).

Mocka os 3 aparelhos externos que ainda não temos:

* **App de Visão Computacional** — substituído pela chamada direta a
  ``planting_service.start_planting`` (faria POST /planting/start).
* **ESP-CAM** — não participa deste fluxo, ignorado.
* **ESP interno** — substituído por um cliente MQTT fake que captura o
  que o backend publica em ``planta/config`` e por chamadas diretas a
  ``mqtt_client._on_message`` com payloads simulados em ``planta/status``
  e ``planta/alerta``.

A persistência é real: o teste grava em Postgres (Neon, ``.env``) e
verifica cada linha. Tudo é limpo no final.

Uso::

    python scripts/test_full_flow.py
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple
from uuid import UUID, uuid4

# Permite executar via ``python scripts/test_full_flow.py`` direto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import mqtt_client
from app.database import (
    plant_repo,
    planta_alerta_repo,
    planta_estufa_repo,
    sensor_reading_repo,
)
from app.db.connection import close_pool, get_pool
from app.db.schema import ensure_schema, ensure_users_table
from app.schemas.plant import PlantCreate
from app.services import (
    plant_service,
    planta_alerta_service,
    planta_status_service,
    planting_service,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("test_full_flow")


# ---------------------------------------------------------------------------
# Fake MQTT client — mocka o ESP interno que escuta planta/config
# ---------------------------------------------------------------------------
@dataclass
class _PublishResult:
    rc: int = 0  # MQTT_ERR_SUCCESS


@dataclass
class _FakeMqttClient:
    """Cliente MQTT em memória: registra cada publish e devolve sucesso."""

    published: List[Tuple[str, dict]] = field(default_factory=list)

    def publish(self, topic: str, payload: str, qos: int = 0) -> _PublishResult:
        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            decoded = payload
        self.published.append((topic, decoded))
        logger.info("[FAKE-ESP] recebeu publish em %s: %s", topic, decoded)
        return _PublishResult()


@dataclass
class _FakeMqttMessage:
    """Imita ``paho.mqtt.client.MQTTMessage`` o suficiente para o roteador."""

    topic: str
    payload: bytes


# ---------------------------------------------------------------------------
# Helpers de asserção
# ---------------------------------------------------------------------------
def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    logger.info("OK %s", message)


# ---------------------------------------------------------------------------
# Setup / teardown
# ---------------------------------------------------------------------------
TEST_PLANT_NAME = f"Test Plant {uuid4().hex[:8]}"


def _seed_test_plant() -> UUID:
    plant = plant_service.create_plant(
        PlantCreate(
            common_name=TEST_PLANT_NAME,
            scientific_name="Testus integratium",
            description="Planta usada apenas no test_full_flow.py",
            optimal_temp_min=18.0,
            optimal_temp_max=28.0,
            optimal_humidity_min=50.0,
            optimal_humidity_max=80.0,
            optimal_soil_moisture_min=40.0,
            optimal_soil_moisture_max=70.0,
            optimal_light_min=300.0,
            optimal_light_max=1200.0,
            watering_interval_hours=12,
        )
    )
    logger.info("Planta de teste criada: id=%s name=%s", plant.id, plant.common_name)
    return plant.id


def _cleanup(plant_id: UUID, estufa_ids: List[UUID]) -> None:
    """Remove tudo que o teste criou (na ordem das FKs)."""
    logger.info("Limpando dados do teste...")
    with get_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM planta_alerta WHERE planta = %s", (TEST_PLANT_NAME,)
        )
        # sensor_reading do teste: device_id IS NULL + recorded_at recente.
        # Aqui apagamos pelos ids salvos no service, mas a forma simples é
        # apagar pelos IDs que coletamos via planta_estufa_repo.
        for eid in estufa_ids:
            cur.execute("DELETE FROM planta_estufa WHERE id = %s", (eid,))
        cur.execute("DELETE FROM plant WHERE id = %s", (plant_id,))


# ---------------------------------------------------------------------------
# Cenários
# ---------------------------------------------------------------------------
def cenario_plantacao(fake: _FakeMqttClient) -> Tuple[UUID, UUID]:
    """Mocka a Visão Computacional disparando /planting/start."""
    logger.info("=== Ciclo de Plantação ===")

    estufa = planting_service.start_planting(TEST_PLANT_NAME, life_days=30)

    # Banco — linha em planta_estufa
    persisted = planta_estufa_repo.get(estufa.id)
    _assert(persisted is not None, "planta_estufa persistida no banco")
    _assert(persisted["life_days"] == 30, "life_days gravado corretamente")
    _assert(persisted["dia_saida"] is None, "dia_saida começa nulo")

    # MQTT — o fake ESP recebeu planta/config
    publishes = [p for p in fake.published if p[0] == "planta/config"]
    _assert(len(publishes) == 1, "backend publicou exatamente 1 planta/config")

    payload = publishes[0][1]
    expected_keys = {
        "nome",
        "vida_dias",
        "solo_min",
        "solo_max",
        "ar_umi_min",
        "ar_umi_max",
        "temp_min",
        "temp_max",
        "luz_min",
        "luz_max",
    }
    _assert(
        set(payload.keys()) == expected_keys,
        f"payload de planta/config tem todas as chaves esperadas ({sorted(expected_keys)})",
    )
    _assert(payload["nome"] == TEST_PLANT_NAME, "nome da planta no payload")
    _assert(payload["vida_dias"] == 30, "vida_dias no payload")
    _assert(payload["temp_min"] == 18.0 and payload["temp_max"] == 28.0, "temp_min/max")
    _assert(payload["luz_min"] == 300.0 and payload["luz_max"] == 1200.0, "luz_min/max")

    return estufa.plant_id, estufa.id


def cenario_status() -> UUID:
    """Mocka o ESP interno publicando em planta/status."""
    logger.info("=== Ciclo de Rotina — planta/status ===")

    status_payload = {
        "planta": TEST_PLANT_NAME,
        "ar_temp": 23.5,
        "ar_umi": 65.0,
        "solo_umi": 55.3,
        "luz_bruta": 880.5,
        "luz_pct": 73.4,
        "bomba": "desligada",
        "estabilizado": True,
        "ts": 1718480000,
    }
    msg = _FakeMqttMessage(
        topic="planta/status", payload=json.dumps(status_payload).encode("utf-8")
    )

    # Roteia pelo on_message real — exatamente o que aconteceria via broker
    mqtt_client._on_message(None, None, msg)

    # Verifica a leitura mais recente
    rows = sensor_reading_repo.list(
        where=lambda r: (
            r.get("device_id") is None
            and r.get("firmware_ts") == status_payload["ts"]
        ),
        order_by="recorded_at",
        descending=True,
        limit=1,
    )
    _assert(len(rows) == 1, "sensor_reading persistido para o planta/status")
    row = rows[0]
    _assert(float(row["temperature_celsius"]) == 23.5, "ar_temp -> temperature_celsius")
    _assert(float(row["humidity_percent"]) == 65.0, "ar_umi -> humidity_percent")
    _assert(
        float(row["soil_moisture_percent"]) == 55.3, "solo_umi -> soil_moisture_percent"
    )
    _assert(float(row["light_lux"]) == 880.5, "luz_bruta -> light_lux")
    _assert(float(row["light_percent"]) == 73.4, "luz_pct -> light_percent")
    _assert(row["pump_state"] == "desligada", "bomba -> pump_state")
    _assert(row["stabilized"] is True, "estabilizado -> stabilized")
    _assert(int(row["firmware_ts"]) == 1718480000, "ts -> firmware_ts")
    _assert(row["status"] == "normal", "status default = normal")
    return row["id"]


def cenario_alerta() -> List[UUID]:
    """Mocka o ESP interno publicando em planta/alerta com 2 itens."""
    logger.info("=== Ciclo de Rotina — planta/alerta ===")

    alerta_payload = {
        "planta": TEST_PLANT_NAME,
        "alertas": [
            {
                "tipo": "umidade_solo",
                "nivel": "warning",
                "mensagem": "Umidade do solo abaixo do mínimo",
                "valor": 32.1,
                "minimo": 40.0,
            },
            {
                "tipo": "temperatura",
                "nivel": "critical",
                "mensagem": "Temperatura muito acima do máximo",
                "valor": 38.0,
                "minimo": None,
            },
        ],
    }
    msg = _FakeMqttMessage(
        topic="planta/alerta", payload=json.dumps(alerta_payload).encode("utf-8")
    )
    mqtt_client._on_message(None, None, msg)

    rows = planta_alerta_repo.list(
        where=lambda r: r["planta"] == TEST_PLANT_NAME,
        order_by="recebido_em",
        descending=True,
    )
    _assert(len(rows) == 2, "planta_alerta: 2 linhas persistidas")
    tipos = {r["tipo"] for r in rows}
    _assert(tipos == {"umidade_solo", "temperatura"}, "tipos persistidos corretamente")
    return [r["id"] for r in rows]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    plant_id: UUID | None = None
    estufa_ids: List[UUID] = []
    sensor_reading_id: UUID | None = None
    alerta_ids: List[UUID] = []

    # Mocka o cliente MQTT — o backend não precisa do broker real.
    fake = _FakeMqttClient()
    mqtt_client._client = fake  # type: ignore[assignment]

    try:
        get_pool()
        ensure_schema()
        ensure_users_table()

        plant_id = _seed_test_plant()
        _, estufa_id = cenario_plantacao(fake)
        estufa_ids.append(estufa_id)
        sensor_reading_id = cenario_status()
        alerta_ids = cenario_alerta()

        logger.info("=== TODOS OS CENÁRIOS PASSARAM ===")
        return 0
    except AssertionError as e:
        logger.error("FALHA: %s", e)
        return 1
    except Exception:
        logger.exception("Erro inesperado no teste")
        return 2
    finally:
        # Cleanup (rola mesmo em caso de falha parcial)
        try:
            with get_pool().connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM planta_alerta WHERE planta = %s", (TEST_PLANT_NAME,)
                )
                if sensor_reading_id is not None:
                    cur.execute(
                        "DELETE FROM sensor_reading WHERE id = %s",
                        (sensor_reading_id,),
                    )
                for eid in estufa_ids:
                    cur.execute("DELETE FROM planta_estufa WHERE id = %s", (eid,))
                if plant_id is not None:
                    cur.execute("DELETE FROM plant WHERE id = %s", (plant_id,))
            logger.info("Cleanup concluído.")
        except Exception:
            logger.exception("Cleanup falhou — pode haver dados órfãos no banco")
        mqtt_client._client = None
        close_pool()


if __name__ == "__main__":
    sys.exit(main())
