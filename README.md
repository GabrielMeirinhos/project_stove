# Stove — Estufa Inteligente com IoT e Visão Computacional

Sistema completo de monitoramento de estufa com sensores IoT, dashboard em tempo real e detecção de doenças em plantas por ML.

---

## Módulos

| Módulo | Descrição | Stack |
|--------|-----------|-------|
| [`frontend/`](frontend/) | Dashboard React com dados em tempo real e visualização 3D | React 19, TypeScript, Tailwind, Three.js |
| [`backend/`](backend/) | API REST + integração MQTT com ESP32 | FastAPI, PostgreSQL (Neon), paho-mqtt |
| [`ml/`](ml/) | Pipeline de classificação de doenças em plantas | TensorFlow, OpenCV, MobileNetV2, TFLite |

## Início Rápido

### Com Docker (recomendado)

```bash
cp .env.example .env
# edite .env com suas credenciais

docker compose up --build
```

| Serviço | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

### Sem Docker

Veja [docs/setup.md](docs/setup.md) para instruções detalhadas por módulo.

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/architecture.md](docs/architecture.md) | Arquitetura completa, fluxo de dados, stack |
| [docs/setup.md](docs/setup.md) | Setup local passo a passo |
| [docs/docker.md](docs/docker.md) | Execução via Docker (dev e prod) |
| [docs/ml.md](docs/ml.md) | Pipeline ML, treinamento e deploy no Raspberry Pi |
| [backend/ENDPOINTS.md](backend/ENDPOINTS.md) | Documentação completa da REST API |
| [backend/docs/ESP32_INTEGRATION.md](backend/docs/ESP32_INTEGRATION.md) | Integração com ESP32 |

## Estrutura

```
project_stove/
├── frontend/          # React + Express + Vite
├── backend/           # FastAPI + PostgreSQL + MQTT
├── ml/                # TensorFlow pipeline
│   ├── training/      # Scripts de treinamento
│   ├── inference/     # Módulo de inferência
│   ├── datasets/      # PlantVillage (gitignored)
│   └── models/        # Pesos treinados (gitignored)
├── docs/              # Documentação técnica
├── infra/             # Futura infra (k8s, terraform)
├── scripts/           # Scripts compartilhados
├── .github/workflows/ # CI/CD GitHub Actions
├── docker-compose.yml
└── .env.example
```

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:
- Credenciais PostgreSQL (Neon)
- Credenciais MQTT (HiveMQ Cloud)
- Gemini API Key (análise de imagens no frontend)
- Kaggle API Key (download do dataset ML)

## Segurança

**Nunca commite o arquivo `.env`.** Ele está no `.gitignore`.
Se credenciais foram expostas no histórico Git, revogue-as imediatamente e use `git filter-repo` para limpar o histórico.
