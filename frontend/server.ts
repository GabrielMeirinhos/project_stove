import "dotenv/config";
import express from "express";
import path from "path";
import * as mqtt from "mqtt";
import { createServer as createViteServer } from "vite";
import { LiveSensorEvent, MqttStatus, SensorData } from "./src/types";

async function startServer() {
  const app = express();
  const PORT = 3000;
  const AUTH_BACKEND_URL = process.env.AUTH_BACKEND_URL ?? "http://127.0.0.1:8005";

  const MQTT_BROKER_HOST = process.env.MQTT_HOST ?? process.env.MQTT_BROKER_HOST ?? "882be47d29a44dff8eb8bf7a5faa9835.s1.eu.hivemq.cloud";
  const MQTT_BROKER_PORT = Number(process.env.MQTT_PORT ?? process.env.MQTT_BROKER_PORT ?? "8883");
  const MQTT_USERNAME = process.env.MQTT_USER ?? process.env.MQTT_USERNAME ?? "projetointegrador";
  const MQTT_PASSWORD = process.env.MQTT_PASSWORD ?? "Integrador123";
  const MQTT_TOPIC_PREFIX = process.env.MQTT_TOPIC_PREFIX ?? "gaia";
  const MQTT_TOPIC = process.env.MQTT_TOPIC ?? `${MQTT_TOPIC_PREFIX}/#`;
  const MQTT_USE_TLS = process.env.MQTT_USE_TLS !== "false";
  const MQTT_URL = process.env.MQTT_URL ?? `${MQTT_USE_TLS ? "mqtts" : "mqtt"}://${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}`;

  let latestSensorData: SensorData | null = null;
  let mqttStatus: MqttStatus = {
    connected: false,
    brokerUrl: MQTT_URL,
    subscribedTopic: MQTT_TOPIC,
    lastMessageAt: null,
  };

  const sseClients = new Set<express.Response>();

  const broadcastLiveEvent = () => {
    const payload: LiveSensorEvent = {
      sensor: latestSensorData,
      status: mqttStatus,
    };

    for (const client of sseClients) {
      client.write(`data: ${JSON.stringify(payload)}\n\n`);
    }
  };

  const applySensorUpdate = (partial: Partial<SensorData>, topic: string) => {
    latestSensorData = {
      moisture: latestSensorData?.moisture ?? 0,
      temperature: latestSensorData?.temperature ?? 0,
      luminosity: latestSensorData?.luminosity ?? 0,
      health: latestSensorData?.health ?? 0,
      ...partial,
      topic,
      source: "mqtt",
      connected: true,
      timestamp: new Date().toISOString(),
    };

    mqttStatus = {
      ...mqttStatus,
      connected: true,
      lastMessageAt: latestSensorData.timestamp,
    };

    broadcastLiveEvent();
  };

  const normalizeValue = (value: unknown) => {
    const numericValue = typeof value === "string" ? Number(value.replace(",", ".")) : Number(value);
    return Number.isFinite(numericValue) ? numericValue : undefined;
  };

  const parseSensorPayload = (topic: string, rawPayload: string): Partial<SensorData> | null => {
    let payload: unknown = rawPayload;

    try {
      payload = JSON.parse(rawPayload);
    } catch {
      payload = rawPayload;
    }

    const updates: Partial<SensorData> = {};

    if (payload && typeof payload === "object" && !Array.isArray(payload)) {
      const record = payload as Record<string, unknown>;

      const moisture = normalizeValue(record.moisture ?? record.humidity ?? record.soilMoisture);
      const temperature = normalizeValue(record.temperature ?? record.temp);
      const luminosity = normalizeValue(record.luminosity ?? record.light ?? record.illuminance);
      const health = normalizeValue(record.health ?? record.healthScore ?? record.vigor);

      if (moisture !== undefined) updates.moisture = moisture;
      if (temperature !== undefined) updates.temperature = temperature;
      if (luminosity !== undefined) updates.luminosity = luminosity;
      if (health !== undefined) updates.health = health;
    }

    if (typeof payload === "string") {
      const scalar = normalizeValue(payload);
      if (scalar !== undefined) {
        if (topic.toLowerCase().includes("moisture") || topic.toLowerCase().includes("humidity")) {
          updates.moisture = scalar;
        } else if (topic.toLowerCase().includes("temp")) {
          updates.temperature = scalar;
        } else if (topic.toLowerCase().includes("light") || topic.toLowerCase().includes("lumen")) {
          updates.luminosity = scalar;
        } else if (topic.toLowerCase().includes("health")) {
          updates.health = scalar;
        }
      }
    }

    return Object.keys(updates).length > 0 ? updates : null;
  };

  const mqttClient = mqtt.connect(MQTT_URL, {
    username: MQTT_USERNAME,
    password: MQTT_PASSWORD,
    reconnectPeriod: 5000,
    connectTimeout: 10000,
  });

  mqttClient.on("connect", () => {
    mqttStatus = {
      ...mqttStatus,
      connected: true,
    };

    mqttClient.subscribe(MQTT_TOPIC, (error) => {
      if (error) {
        console.error("MQTT subscribe error:", error.message);
        mqttStatus = {
          ...mqttStatus,
          connected: false,
        };
        broadcastLiveEvent();
        return;
      }

      broadcastLiveEvent();
      console.log(`MQTT connected to ${MQTT_URL} and subscribed to ${MQTT_TOPIC}`);
    });
  });

  mqttClient.on("message", (topic, payload) => {
    const message = payload.toString();
    const parsed = parseSensorPayload(topic, message);

    if (parsed) {
      applySensorUpdate(parsed, topic);
      return;
    }

    mqttStatus = {
      ...mqttStatus,
      connected: true,
      lastMessageAt: new Date().toISOString(),
    };

    broadcastLiveEvent();
  });

  mqttClient.on("error", (error) => {
    console.error("MQTT connection error:", error.message);
    mqttStatus = {
      ...mqttStatus,
      connected: false,
    };
    broadcastLiveEvent();
  });

  mqttClient.on("close", () => {
    mqttStatus = {
      ...mqttStatus,
      connected: false,
    };
    broadcastLiveEvent();
  });

  app.use(express.json());

  const proxyAuthRequest = async (req: express.Request, res: express.Response, next: express.NextFunction) => {
    const targetUrl = new URL(req.originalUrl, AUTH_BACKEND_URL);
    const headers = new Headers();

    for (const [key, value] of Object.entries(req.headers)) {
      if (value == null) {
        continue;
      }

      const normalizedKey = key.toLowerCase();
      if (normalizedKey === "host" || normalizedKey === "connection" || normalizedKey === "content-length") {
        continue;
      }

      headers.set(key, Array.isArray(value) ? value.join(",") : value);
    }

    const hasBody = req.method !== "GET" && req.method !== "HEAD" && req.body !== undefined;

    if (hasBody && !headers.has("content-type")) {
      headers.set("content-type", "application/json");
    }

    try {
      const upstreamResponse = await fetch(targetUrl, {
        method: req.method,
        headers,
        body: hasBody ? JSON.stringify(req.body) : undefined,
        redirect: "manual",
      });

      res.status(upstreamResponse.status);

      upstreamResponse.headers.forEach((value, key) => {
        const normalizedKey = key.toLowerCase();
        if (normalizedKey === "content-encoding" || normalizedKey === "transfer-encoding" || normalizedKey === "connection") {
          return;
        }

        res.setHeader(key, value);
      });

      if (upstreamResponse.body) {
        const body = Buffer.from(await upstreamResponse.arrayBuffer());
        res.send(body);
        return;
      }

      res.end();
    } catch (error) {
      next(error);
    }
  };

  app.all("/api/auth/*", proxyAuthRequest);
  app.all("/api/admin/*", proxyAuthRequest);

  app.get("/api/dados", (req, res) => {
    res.json(latestSensorData);
  });

  app.get("/api/mqtt/status", (req, res) => {
    res.json(mqttStatus);
  });

  app.get("/api/live/stream", (req, res) => {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders?.();

    sseClients.add(res);
    res.write(`data: ${JSON.stringify({ sensor: latestSensorData, status: mqttStatus })}\n\n`);

    req.on("close", () => {
      sseClients.delete(res);
      res.end();
    });
  });

  app.get("/api/modelo-atual", (req, res) => {
    const day = req.query.day || "1";
    res.json({
      day: parseInt(day as string, 10),
      modelPath: `/models/plant_day_${day}.glb`,
      scale: 1 + (parseInt(day as string, 10) - 1) * 0.5,
    });
  });

  app.get("/api/historico", (req, res) => {
    const history = Array.from({ length: 7 }, (_, i) => ({
      day: `Dia ${i + 1}`,
      growth: 10 + i * 5 + Math.random() * 2,
      moisture: 40 + Math.random() * 20,
      health: 80 + Math.random() * 20,
    }));
    res.json(history);
  });

  const ML_INFERENCE_URL = process.env.ML_INFERENCE_URL ?? "http://localhost:8001";

  app.post("/api/analyze-image", async (req, res) => {
    const { image_b64 } = req.body as { image_b64?: string };
    if (!image_b64) {
      res.status(400).json({ error: "image_b64 obrigatório" });
      return;
    }

    try {
      const mlRes = await fetch(`${ML_INFERENCE_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_b64 }),
        signal: AbortSignal.timeout(15_000),
      });

      if (!mlRes.ok) {
        const text = await mlRes.text();
        res.status(mlRes.status).json({ error: text });
        return;
      }

      const result = await mlRes.json();
      res.json(result);
    } catch (err) {
      console.error("ML inference error:", err);
      // Fallback: retorna mock para não travar o frontend
      res.json({
        top_prediction: { class: "Servico_indisponivel", confidence: 0 },
        top_k: [{ class: "Servico_indisponivel", confidence: 0 }],
        inference_ms: 0,
        mock: true,
      });
    }
  });

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
