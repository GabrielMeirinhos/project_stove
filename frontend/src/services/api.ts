import * as mqtt from 'mqtt';
import { SensorData, HistoryData, LiveSensorEvent, MqttStatus, PlantAnalysis, PlantStatusPayload } from '../types';

const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL ?? '/api/v1';
const AUTH_BASE_URL = import.meta.env.VITE_AUTH_API_URL ?? '/api';
const PLANT_WS_BASE_URL = import.meta.env.VITE_PLANT_WS_URL ?? import.meta.env.VITE_BACKEND_WS_URL ?? '';
const MQTT_WS_URL = import.meta.env.VITE_MQTT_WS_URL ?? import.meta.env.VITE_MQTT_URL ?? '';
const MQTT_USERNAME = import.meta.env.VITE_MQTT_USER ?? '';
const MQTT_PASSWORD = import.meta.env.VITE_MQTT_PASSWORD ?? '';
const MQTT_CLIENT_ID = import.meta.env.VITE_MQTT_CLIENT_ID ?? 'gaia-frontend';
const MQTT_TOPIC_PREFIX = import.meta.env.VITE_MQTT_TOPIC_PREFIX ?? 'planta';
const PLANT_STATUS_TOPIC = `${MQTT_TOPIC_PREFIX}/status`;
const PLANT_ALERT_TOPIC = `${MQTT_TOPIC_PREFIX}/alerta`;

export interface RealtimeSubscription {
  close(): void;
  onerror?: (error?: unknown) => void;
}

export type AuthRole = 'admin' | 'user';

export interface AuthUser {
  id: string;
  full_name: string;
  email: string;
  role: AuthRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in_minutes: number;
  user: AuthUser;
}

export interface AdminOverview {
  users_total: number;
  admins_total: number;
  active_users_total: number;
  pending_invites_total: number;
  pending_reset_tokens_total: number;
}

type BackendSensorReading = {
  soil_moisture_percent?: number | null;
  humidity_percent?: number | null;
  temperature_celsius?: number | null;
  light_lux?: number | null;
  status?: 'normal' | 'warning' | 'critical';
  recorded_at: string;
};

const roundValue = (value: number) => Math.round(value);

const formatDayLabel = (date: Date) =>
  date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });

const clampToPercentage = (value: number) => Math.min(100, Math.max(0, value));

const getDefaultWebSocketBaseUrl = () => {
  if (typeof window === 'undefined') {
    return '';
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
};

const buildWebSocketUrl = (topic: string) => {
  const baseUrl = PLANT_WS_BASE_URL || getDefaultWebSocketBaseUrl();
  const normalizedBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const normalizedTopic = topic.startsWith('/') ? topic.slice(1) : topic;
  return `${normalizedBase}/${normalizedTopic}`;
};

const parseRealtimePayload = (data: MessageEvent['data']) => {
  if (typeof data !== 'string') {
    return data;
  }

  try {
    return JSON.parse(data);
  } catch {
    return data;
  }
};

const getMqttBrokerUrl = () => MQTT_WS_URL;

const isBridgeTransportConfigured = () => Boolean(PLANT_WS_BASE_URL);

const isMqttTransportConfigured = () => Boolean(getMqttBrokerUrl());

const parseAlertMessage = (payload: unknown) => {
  if (typeof payload === 'string') {
    return payload;
  }

  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const record = payload as { message?: unknown; alerta?: unknown; text?: unknown; detail?: unknown };
  const message = record.message ?? record.alerta ?? record.text ?? record.detail;
  return typeof message === 'string' ? message : null;
};

const createWebSocketSubscription = (
  topic: string,
  onMessage: (payload: unknown) => void,
): RealtimeSubscription => {
  const source = new WebSocket(buildWebSocketUrl(topic));
  const subscription: RealtimeSubscription = {
    close: () => source.close(),
  };

  source.onmessage = (event) => {
    const payload = parseRealtimePayload(event.data);
    onMessage(payload);
  };

  source.onerror = (event) => {
    subscription.onerror?.(event);
  };

  return subscription;
};

const createMqttSubscription = (
  topic: string,
  onMessage: (payload: unknown) => void,
): RealtimeSubscription => {
  const brokerUrl = getMqttBrokerUrl();
  const client = mqtt.connect(brokerUrl, {
    clientId: MQTT_CLIENT_ID,
    username: MQTT_USERNAME || undefined,
    password: MQTT_PASSWORD || undefined,
    reconnectPeriod: 5000,
    connectTimeout: 10000,
  });

  const subscription: RealtimeSubscription = {
    close: () => client.end(true),
  };

  client.on('connect', () => {
    client.subscribe(topic, { qos: 1 }, (error) => {
      if (error) {
        subscription.onerror?.(error);
      }
    });
  });

  client.on('message', (receivedTopic, payload) => {
    if (receivedTopic !== topic) {
      return;
    }

    onMessage(parseRealtimePayload(payload.toString('utf8')));
  });

  client.on('error', (error) => {
    subscription.onerror?.(error);
  });

  return subscription;
};

const getRealtimeBrokerUrl = () => getMqttBrokerUrl() || (PLANT_WS_BASE_URL || getDefaultWebSocketBaseUrl());

export const mapPlantStatusToSensor = (payload: PlantStatusPayload): SensorData => {
  const lightValue = payload.luz_bruta > 0 ? payload.luz_bruta : payload.luz_pct;
  const estimatedHealth = payload.estabilizado
    ? 96
    : Math.min(100, Math.max(45, Math.round((payload.solo_umi * 0.45) + ((100 - Math.abs(payload.ar_temp - 24)) * 2.5) + (payload.luz_pct * 0.2))));
  const timestamp = payload.ts > 1_000_000_000_000 ? new Date(payload.ts).toISOString() : new Date().toISOString();

  return {
    moisture: payload.solo_umi,
    temperature: payload.ar_temp,
    luminosity: lightValue,
    health: estimatedHealth,
    timestamp,
    source: 'mqtt',
    topic: 'planta/status',
    connected: true,
  };
};

const normalizeReadingValue = (value: number | null | undefined) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }

  return value;
};

const buildHistoryFromReadings = (readings: BackendSensorReading[]): HistoryData[] => {
  const byDay = new Map<
    string,
    {
      label: string;
      moistureValues: number[];
      humidityValues: number[];
      normalCount: number;
      totalCount: number;
    }
  >();

  readings.forEach((reading) => {
    const recordedAt = new Date(reading.recorded_at);
    if (Number.isNaN(recordedAt.getTime())) {
      return;
    }

    const dayKey = recordedAt.toISOString().slice(0, 10);
    const existing = byDay.get(dayKey) ?? {
      label: formatDayLabel(recordedAt),
      moistureValues: [],
      humidityValues: [],
      normalCount: 0,
      totalCount: 0,
    };

    const soilMoisture = normalizeReadingValue(reading.soil_moisture_percent);
    const humidity = normalizeReadingValue(reading.humidity_percent);

    if (soilMoisture !== null) {
      existing.moistureValues.push(soilMoisture);
    }

    if (humidity !== null) {
      existing.humidityValues.push(humidity);
    }

    existing.totalCount += 1;
    if (reading.status === 'normal') {
      existing.normalCount += 1;
    }

    byDay.set(dayKey, existing);
  });

  return Array.from(byDay.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .slice(-7)
    .map(([, bucket]) => {
      const averageMoisture = bucket.moistureValues.length
        ? bucket.moistureValues.reduce((sum, value) => sum + value, 0) / bucket.moistureValues.length
        : 0;

      const averageHumidity = bucket.humidityValues.length
        ? bucket.humidityValues.reduce((sum, value) => sum + value, 0) / bucket.humidityValues.length
        : averageMoisture;

      const growthScore = clampToPercentage(averageMoisture);
      const healthScore = bucket.totalCount > 0 ? (bucket.normalCount / bucket.totalCount) * 100 : 0;

      return {
        day: bucket.label,
        growth: roundValue(growthScore),
        moisture: roundValue(averageHumidity),
        health: roundValue(healthScore),
      };
    });
};

export const api = {
  async authLogin(email: string, password: string): Promise<AuthLoginResponse> {
    const res = await fetch(`${AUTH_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Credenciais inválidas');
    return res.json();
  },

  async authMe(token: string): Promise<AuthUser> {
    const res = await fetch(`${AUTH_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Sessão inválida');
    return res.json();
  },

  async adminUsers(token: string): Promise<AuthUser[]> {
    const res = await fetch(`${AUTH_BASE_URL}/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Falha ao buscar usuários');
    return res.json();
  },

  async adminOverview(token: string): Promise<AdminOverview> {
    const res = await fetch(`${AUTH_BASE_URL}/admin/overview`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Falha ao buscar resumo administrativo');
    return res.json();
  },

  async getSensors(): Promise<SensorData | null> {
    const res = await fetch('/api/dados');
    if (!res.ok) throw new Error('Falha ao buscar sensores');
    return res.json();
  },

  async getMqttStatus(): Promise<MqttStatus> {
    const res = await fetch('/api/mqtt/status');
    if (!res.ok) throw new Error('Falha ao buscar status MQTT');
    return res.json();
  },

  async getHistory(token?: string): Promise<HistoryData[]> {
    const res = await fetch(`${BACKEND_BASE_URL}/sensor-readings?limit=1000`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error('Falha ao buscar historico');

    const readings = (await res.json()) as BackendSensorReading[];
    return buildHistoryFromReadings(readings);
  },

  async getModelInfo(day: number) {
    const res = await fetch(`/api/modelo-atual?day=${day}`);
    if (!res.ok) throw new Error('Falha ao buscar informacoes do modelo');
    return res.json();
  },

  async analyzeImage(imageB64: string): Promise<PlantAnalysis> {
    const res = await fetch('/api/analyze-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_b64: imageB64 }),
    });
    if (!res.ok) throw new Error('Falha na análise de imagem');
    return res.json();
  },

  getRealtimeConnectionInfo() {
    return {
      brokerUrl: getRealtimeBrokerUrl(),
      statusTopic: PLANT_STATUS_TOPIC,
      alertTopic: PLANT_ALERT_TOPIC,
    };
  },

  subscribePlantStatus(onMessage: (payload: PlantStatusPayload) => void) {
    if (isMqttTransportConfigured() && !isBridgeTransportConfigured()) {
      return createMqttSubscription(PLANT_STATUS_TOPIC, (payload) => {
        if (payload && typeof payload === 'object') {
          onMessage(payload as PlantStatusPayload);
        }
      });
    }

    return createWebSocketSubscription('planta/status', (payload) => {
      if (payload && typeof payload === 'object') {
        onMessage(payload as PlantStatusPayload);
      }
    });
  },

  subscribePlantAlert(onMessage: (message: string) => void) {
    if (isMqttTransportConfigured() && !isBridgeTransportConfigured()) {
      return createMqttSubscription(PLANT_ALERT_TOPIC, (payload) => {
        const message = parseAlertMessage(payload);
        if (message) {
          onMessage(message);
        }
      });
    }

    return createWebSocketSubscription('planta/alerta', (payload) => {
      const message = parseAlertMessage(payload);
      if (message) {
        onMessage(message);
      }
    });
  },

  subscribeSensorStream(onMessage: (event: LiveSensorEvent) => void) {
    const source = new EventSource('/api/live/stream');

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as LiveSensorEvent;
      onMessage(payload);
    };

    return source;
  }
};
