import { SensorData, HistoryData, LiveSensorEvent, MqttStatus, PlantAnalysis } from '../types';

const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000/api/v1';
const AUTH_BASE_URL = import.meta.env.VITE_AUTH_API_URL ?? '/api';

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

  async getHistory(): Promise<HistoryData[]> {
    const url = new URL(`${BACKEND_BASE_URL}/sensor-readings`);
    url.searchParams.set('limit', '1000');

    const res = await fetch(url.toString());
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

  subscribeSensorStream(onMessage: (event: LiveSensorEvent) => void) {
    const source = new EventSource('/api/live/stream');

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as LiveSensorEvent;
      onMessage(payload);
    };

    return source;
  }
};
