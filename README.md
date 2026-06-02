# Stove — Estufa Inteligente com IoT e Visão Computacional

Sistema completo de monitoramento de estufa com sensores IoT, dashboard em tempo real, autenticação JWT com controle de acesso por perfil e detecção de doenças em plantas por ML.

---

## Módulos

| Módulo | Descrição | Stack |
|--------|-----------|-------|
| [`frontend/`](frontend/) | Dashboard React com dados em tempo real via MQTT/SSE | React 19, TypeScript, Tailwind, Three.js, Express |
| [`backend/`](backend/) | API REST com autenticação JWT + integração MQTT | FastAPI, PostgreSQL, paho-mqtt, python-jose |
| [`ml/`](ml/) | Pipeline de classificação de doenças em plantas | TensorFlow, OpenCV, MobileNetV2, TFLite |

---

## Início Rápido

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais. Os campos obrigatórios são:

| Variável | Descrição |
|----------|-----------|
| `MQTT_HOST` | Host do broker HiveMQ Cloud |
| `MQTT_USER` / `MQTT_PASSWORD` | Credenciais MQTT |
| `SECRET_KEY` | Chave JWT (gere com `openssl rand -hex 32`) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Usuário superadmin inicial |
| `GEMINI_API_KEY` | Chave da API Gemini (opcional) |

Os valores de PostgreSQL já têm defaults para o container Docker local.

### 2. Subir localmente

```bash
# Desenvolvimento (hot-reload + portas expostas no host)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Apenas produção local (sem portas expostas)
docker compose up -d
```

| Serviço | URL (dev) |
|---------|-----------|
| Dashboard | http://localhost:3000 |
| API / Swagger | http://localhost:8000 / http://localhost:8000/docs |

### 3. Deploy em produção (Coolify)

Use o arquivo `docker-compose.prod.yml` no painel do Coolify e configure as variáveis de ambiente listadas acima. O Traefik do Coolify cuida do roteamento — nenhuma porta é exposta diretamente.

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## Autenticação

A API utiliza **JWT stateless**. O token é obtido via login e deve ser enviado em todas as requisições protegidas.

```bash
# Obter token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<senha>"

# Usar token
curl http://localhost:8000/api/v1/plants \
  -H "Authorization: Bearer <token>"
```

### Perfis de acesso

| Perfil | Acesso |
|--------|--------|
| `superadmin` | Acesso total a todos os recursos e usuários |
| `user` | Acesso apenas aos próprios recursos (plantas, devices vinculados, leituras, alertas) |

Usuários são criados exclusivamente por superadmin via `POST /api/v1/users`.

---

## Variáveis de Ambiente

```env
# PostgreSQL (container Docker local)
PGHOST=postgres
PGDATABASE=stovedb
PGUSER=stove
PGPASSWORD=<senha>
PGSSLMODE=disable
PGCHANNELBINDING=disable

# MQTT (HiveMQ Cloud)
MQTT_HOST=<cluster>.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USER=<usuario>
MQTT_PASSWORD=<senha>
MQTT_USE_TLS=true
MQTT_CLIENT_ID=gaia-backend
MQTT_TOPIC_PREFIX=gaia

# JWT / Autenticação
SECRET_KEY=<chave-aleatoria-min-32-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<senha-forte>

# Frontend
GEMINI_API_KEY=<chave-gemini>
APP_URL=https://<seu-dominio>
```

---

## Estrutura

```
project_stove/
├── frontend/              # React + Express + Vite
├── backend/               # FastAPI + PostgreSQL + MQTT
│   ├── app/
│   │   ├── auth.py        # JWT, bcrypt, dependências de acesso
│   │   ├── routers/       # Endpoints REST (auth, users, plants, ...)
│   │   ├── services/      # Regras de negócio
│   │   ├── schemas/       # Modelos Pydantic
│   │   └── db/            # Pool, repositório genérico, bootstrap
│   └── SQL/
│       └── schema.sql     # Schema PostgreSQL completo
├── ml/                    # Pipeline TensorFlow
│   ├── training/
│   ├── inference/
│   ├── datasets/          # gitignored
│   └── models/            # gitignored
├── openapi.json           # Spec OpenAPI gerada do backend
├── docker-compose.yml     # Base
├── docker-compose.dev.yml # Override de desenvolvimento (portas expostas, hot-reload)
├── docker-compose.prod.yml# Configuração para Coolify (sem port bindings)
└── .env.example
```

---

## OpenAPI

O arquivo [`openapi.json`](openapi.json) na raiz contém a especificação completa da API. Use-o para:
- Gerar um client TypeScript com `openapi-typescript`
- Importar no Postman/Insomnia para testes
- Visualizar no [Swagger Editor](https://editor.swagger.io)

---

## Segurança

- **Nunca commite o arquivo `.env`.** Ele está no `.gitignore`.
- Regenere a `SECRET_KEY` em produção com `openssl rand -hex 32`.
- Se credenciais foram expostas no histórico Git, revogue-as imediatamente.
