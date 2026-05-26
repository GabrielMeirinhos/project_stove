# Arquitetura do Sistema — Stove (Estufa Inteligente)

## Visão Geral

Sistema IoT de monitoramento e controle de estufa com detecção de doenças por visão computacional.

```
┌─────────────────────────────────────────────────────────────────┐
│                         DISPOSITIVOS                            │
│  ESP32 (sensores: temp, umidade, solo, luz) + câmera           │
└────────────────────────────┬────────────────────────────────────┘
                             │ MQTT / TLS (HiveMQ Cloud)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  • Recebe dados MQTT                                            │
│  • REST API /api/v1/*                                           │
│  • Gera alertas automáticos                                     │
│  • Persiste no PostgreSQL (Neon)                                │
└──────────────┬──────────────────────────┬───────────────────────┘
               │ HTTP (REST)              │ PostgreSQL (psycopg3)
               ▼                          ▼
┌──────────────────────┐      ┌──────────────────────────────────┐
│   FRONTEND (React)   │      │        DATABASE (Neon)           │
│  • Dashboard RT      │      │  PostgreSQL serverless           │
│  • 3D plant view     │      │  8 tabelas: plant, device,       │
│  • Alertas           │      │  sensor_reading, irrigation,     │
│  • SSE (live update) │      │  plant_image, vision_analysis,   │
│  • MQTT client       │      │  system_event, alert             │
└──────────────────────┘      └──────────────────────────────────┘
               │
               │ Imagens (POST /api/v1/images)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ML PIPELINE (Python)                         │
│  • MobileNetV2 transfer learning                                │
│  • Dataset: PlantVillage (Kaggle)                               │
│  • Exporta: TFLite INT8 para Raspberry Pi                       │
│  • Inferência: ~50ms, modelo ~3.5MB                             │
└─────────────────────────────────────────────────────────────────┘
```

## Módulos

### `frontend/`
- **Runtime**: Node.js + Express (servidor) + Vite (build)
- **UI**: React 19 + TypeScript + Tailwind CSS
- **3D**: React Three Fiber + Three.js (visualização procedural da planta)
- **Charts**: Recharts
- **Comunicação**: REST (fetch) + SSE (Server-Sent Events para dados live) + MQTT direto

### `backend/`
- **Framework**: FastAPI 0.115
- **Banco**: PostgreSQL via psycopg3 + connection pool
- **MQTT**: paho-mqtt (subscriber de dados do ESP32)
- **Padrão**: Router → Service → Repository (CRUD genérico)
- **Routers**: plants, devices, sensor_readings, irrigation, images, vision, system_events, alerts

### `ml/`
- **Framework**: TensorFlow + OpenCV + scikit-learn
- **Backbone**: MobileNetV2 (pré-treinado ImageNet)
- **Treinamento em 2 fases**: backbone congelado → descongelamento parcial
- **Destino de deploy**: Raspberry Pi (TFLite INT8, ~50ms/inferência)

## Fluxo de Dados

1. ESP32 coleta sensores → publica via MQTT (`gaia/<device_id>/sensors`)
2. Backend recebe, valida, persiste no banco e gera alertas
3. Frontend faz polling/SSE e exibe dados em tempo real
4. Câmera captura foto → upload para backend → análise via modelo ML → `vision_analysis`

## Tecnologias

| Camada | Stack | Versão |
|--------|-------|--------|
| Frontend | React + TypeScript + Vite + Express | 19 / 5.8 / 6.2 |
| Backend | FastAPI + Uvicorn + Pydantic | 0.115 / 0.32 / 2.9 |
| Database | PostgreSQL (Neon serverless) | psycopg3 3.2 |
| MQTT | paho-mqtt + HiveMQ Cloud | 2.1 |
| ML | TensorFlow + OpenCV + scikit-learn | latest |
| IoT | ESP32 (firmware não incluso neste repo) | — |
| Container | Docker + Docker Compose | 27+ |
| CI | GitHub Actions | — |
