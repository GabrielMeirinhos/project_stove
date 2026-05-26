export interface SensorData {
  moisture: number;
  temperature: number;
  luminosity: number;
  health: number;
  timestamp: string;
  source?: 'mqtt' | 'mock';
  topic?: string;
  connected?: boolean;
}

export interface HistoryData {
  day: string;
  growth: number;
  moisture: number;
  health: number;
}

export interface ModelInfo {
  day: number;
  modelPath: string;
  scale: number;
}

export interface MqttStatus {
  connected: boolean;
  brokerUrl: string;
  subscribedTopic: string;
  lastMessageAt: string | null;
}

export interface LiveSensorEvent {
  sensor: SensorData | null;
  status: MqttStatus;
}

export interface PlantPrediction {
  class: string;
  confidence: number;
}

export interface PlantAnalysis {
  top_prediction: PlantPrediction;
  top_k: PlantPrediction[];
  inference_ms: number;
  mock: boolean;
}
