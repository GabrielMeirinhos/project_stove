import "dotenv/config";
import * as mqtt from "mqtt";

const MQTT_BROKER_HOST = process.env.MQTT_HOST ?? process.env.MQTT_BROKER_HOST ?? "882be47d29a44dff8eb8bf7a5faa9835.s1.eu.hivemq.cloud";
const MQTT_BROKER_PORT = Number(process.env.MQTT_PORT ?? process.env.MQTT_BROKER_PORT ?? "8883");
const MQTT_USERNAME = process.env.MQTT_USER ?? process.env.MQTT_USERNAME ?? "projetointegrador";
const MQTT_PASSWORD = process.env.MQTT_PASSWORD ?? "Integrador123";
const MQTT_TOPIC_PREFIX = process.env.MQTT_TOPIC_PREFIX ?? "gaia";
const MQTT_TOPIC = process.env.MQTT_SIM_TOPIC ?? `${MQTT_TOPIC_PREFIX}/simulator/telemetry`;
const MQTT_USE_TLS = process.env.MQTT_USE_TLS !== "false";
const MQTT_URL = process.env.MQTT_URL ?? `${MQTT_USE_TLS ? "mqtts" : "mqtt"}://${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}`;
const INTERVAL_MS = Number(process.env.MQTT_SIM_INTERVAL_MS ?? "2000");

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

let state = {
  moisture: 42,
  temperature: 24,
  luminosity: 760,
  health: 86,
};

const nextPayload = () => {
  state = {
    moisture: clamp(state.moisture + (Math.random() * 6 - 3), 15, 95),
    temperature: clamp(state.temperature + (Math.random() * 1.6 - 0.8), 12, 45),
    luminosity: clamp(state.luminosity + (Math.random() * 120 - 60), 80, 1800),
    health: clamp(state.health + (Math.random() * 4 - 2), 20, 100),
  };

  return {
    moisture: Number(state.moisture.toFixed(2)),
    temperature: Number(state.temperature.toFixed(2)),
    luminosity: Number(state.luminosity.toFixed(2)),
    health: Number(state.health.toFixed(2)),
    timestamp: new Date().toISOString(),
    deviceId: "gaia-sim-01",
  };
};

const client = mqtt.connect(MQTT_URL, {
  username: MQTT_USERNAME,
  password: MQTT_PASSWORD,
  reconnectPeriod: 5000,
  connectTimeout: 10000,
});

client.on("connect", () => {
  console.log(`Connected to ${MQTT_URL}`);
  console.log(`Publishing simulated sensor data on topic: ${MQTT_TOPIC}`);

  const publish = () => {
    const payload = nextPayload();
    client.publish(MQTT_TOPIC, JSON.stringify(payload), { qos: 0 }, (error) => {
      if (error) {
        console.error("Publish error:", error.message);
        return;
      }

      console.log(`Published: ${JSON.stringify(payload)}`);
    });
  };

  publish();
  setInterval(publish, INTERVAL_MS);
});

client.on("error", (error) => {
  console.error("MQTT simulator connection error:", error.message);
});

client.on("reconnect", () => {
  console.log("Reconnecting MQTT simulator...");
});
