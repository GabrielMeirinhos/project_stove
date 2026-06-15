import { SensorData, HistoryData, MqttStatus, PlantAnalysis, PlantStatusPayload } from '../types';

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
const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL ?? '/api/v1';
const AUTH_BASE_URL = import.meta.env.VITE_AUTH_API_URL ?? '/api';

export interface RealtimeSubscription {
  close(): void;
  onerror?: (error?: unknown) => void;
}
export interface RealtimeSubscription {
  close(): void;
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
type BackendSensorReading = {
  soil_moisture_percent?: number | null;
  humidity_percent?: number | null;
  temperature_celsius?: number | null;
  light_lux?: number | null;
  status?: 'normal' | 'warning' | 'critical';
  recorded_at: string;
};

interface LiveStreamMessage {
  eventType?: 'status' | 'alert';
  topic?: string;
  data?: unknown;
  sensor?: SensorData | null;
  status?: MqttStatus;
  message?: string;
}


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

const roundValue = (value: number) => Math.round(value);

const formatDayLabel = (date: Date) =>
  date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });

const clampToPercentage = (value: number) => Math.min(100, Math.max(0, value));
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
      getRealtimeConnectionInfo() {
        return {
          streamUrl: '/api/live/stream',
          statusTopic: 'planta/status',
          alertTopic: 'planta/alerta',
        };
      },
    };
  },

  /**
   * Subscreve ao stream SSE de tempo real para status de planta e alertas.
   * O stream discrimina mensagens por eventType/topic.
   * Não usa WebSocket ou MQTT direto no cliente - apenas SSE.
   */
  subscribeLiveStream(
    onStatus: (payload: PlantStatusPayload) => void,
    onAlert: (message: string) => void,
  ): RealtimeSubscription {
    const source = new EventSource('/api/live/stream');
    
    source.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as LiveStreamMessage;
        
        // Discrimina por eventType ou topic
        if (message.eventType === 'status' || message.topic === 'planta/status') {
          // Se vem com campo data, usa isso; senão tenta montar de sensor + status
          if (message.data && typeof message.data === 'object') {
            onStatus(message.data as PlantStatusPayload);
          }
        } else if (message.eventType === 'alert' || message.topic === 'planta/alerta') {
          const alertMsg = typeof message.data === 'string' 
            ? message.data 
            : parseAlertMessage(message.data);
          if (alertMsg) {
            onAlert(alertMsg);
          }
        }
      } catch (err) {
        console.error('[SSE] Erro ao processar mensagem:', err);
      }
    };
    
    source.onerror = () => {
      console.error('[SSE] Conexão encerrada');
      source.close();
    };

    return {
      close: () => source.close(),
    };
  },
};
