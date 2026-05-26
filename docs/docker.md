# Execução via Docker

## Pré-requisitos

- Docker 27+
- Docker Compose v2 (`docker compose`, não `docker-compose`)

## Desenvolvimento (hot-reload)

```bash
# Copie e edite as variáveis
cp .env.example .env

# Sobe frontend + backend (override de dev aplicado automaticamente)
docker compose up --build

# Com o módulo ML também:
docker compose --profile ml up --build
```

O `docker-compose.override.yml` é aplicado automaticamente e configura volumes para hot-reload.

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

## Produção

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Em produção:
- Frontend: imagem compilada (Vite build incluído na imagem)
- Backend: sem reload automático
- `restart: always` em ambos os serviços

## Comandos úteis

```bash
# Ver logs de um serviço
docker compose logs -f backend

# Entrar no container do backend
docker compose exec backend bash

# Parar tudo
docker compose down

# Parar e remover volumes (ML datasets/models)
docker compose down -v

# Rebuild de um serviço específico
docker compose up --build backend
```

## Volumes persistentes

| Volume | Conteúdo |
|--------|----------|
| `ml-datasets` | Dataset PlantVillage |
| `ml-models` | Pesos treinados (.keras, .tflite) |
| `ml-checkpoints` | Checkpoints de treinamento |
| `ml-outputs` | Métricas, plots, relatórios |

## Estrutura dos arquivos Docker

```
project_stove/
├── docker-compose.yml          # Serviços base
├── docker-compose.override.yml # Dev (hot-reload)
├── docker-compose.prod.yml     # Produção
├── frontend/
│   ├── Dockerfile              # Multi-stage: deps → builder → runner
│   └── .dockerignore
├── backend/
│   ├── Dockerfile
│   └── .dockerignore
└── ml/
    ├── Dockerfile
    └── .dockerignore
```
