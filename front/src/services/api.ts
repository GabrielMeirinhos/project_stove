import { SensorData, HistoryData, LiveSensorEvent, MqttStatus } from '../types';

export const api = {
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
    const res = await fetch('/api/historico');
    if (!res.ok) throw new Error('Falha ao buscar historico');
    return res.json();
  },

  async getModelInfo(day: number) {
    const res = await fetch(`/api/modelo-atual?day=${day}`);
    if (!res.ok) throw new Error('Falha ao buscar informacoes do modelo');
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
