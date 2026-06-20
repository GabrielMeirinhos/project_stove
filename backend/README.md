# Backend — Sistema de Monitoramento de Estufa Inteligente

API REST em **Python + FastAPI** com autenticação JWT, controle de acesso por perfil (RBAC), integração MQTT com ESP32 e persistência em PostgreSQL.

---

## Stack

- **FastAPI 0.115** — framework web ASGI
- **PostgreSQL** via `psycopg 3` + `psycopg-pool`
- **paho-mqtt 2.1** — integração com broker HiveMQ Cloud
- **python-jose** — geração e validação de JWT
- **bcrypt** — hash de senhas

---

## Estrutura

```
backend/
├── app/
│   ├── main.py              # Lifespan, registro de routers, CORS
│   ├── config.py            # Leitura de variáveis de ambiente
│   ├── auth.py              # JWT, bcrypt, dependências get_current_user / require_superadmin
│   ├── database.py          # Singletons de repositório por tabela
│   ├── mqtt_client.py       # Cliente MQTT (HiveMQ Cloud)
│   ├── db/
│   │   ├── connection.py    # Pool psycopg-pool
│   │   ├── repository.py    # PostgresRepository (CRUD genérico)
│   │   └── schema.py        # Bootstrap idempotente do schema + seed do admin
│   ├── schemas/             # Modelos Pydantic por entidade
│   │   ├── user.py
│   │   ├── plant.py
│   │   └── ...
│   ├── services/            # Regras de negócio por entidade
│   └── routers/             # Endpoints REST por entidade
│       ├── auth.py          # POST /auth/login
│       ├── users.py         # POST/GET /users (superadmin)
│       ├── plants.py
│       └── ...
└── SQL/
    └── schema.sql           # Schema PostgreSQL completo
```

---

## Autenticação e Autorização

### Fluxo JWT

1. `POST /api/v1/auth/login` com `username` e `password` (form data)
2. Retorna `{ access_token, token_type: "bearer" }`
3. Todas as requisições protegidas exigem header `Authorization: Bearer <token>`

O token é **stateless** — contém `username`, `role` e `user_id`. Expira em `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão: 60 min).

### Perfis (roles)

| Role | Descrição |
|------|-----------|
| `superadmin` | Acesso total; gerencia usuários e devices |
| `user` | Acesso apenas aos próprios recursos |

### Regras por recurso

| Recurso | `user` | `superadmin` |
|---------|--------|-------------|
| `plants` | CRUD dos próprios | CRUD de todos |
| `devices` | Leitura filtrada pelas suas plantas | CRUD de todos |
| `sensor_readings`, `alerts`, `irrigation_events`, `images` | Filtrado pelos seus devices | Tudo |
| `vision_analyses` | Filtrado pelas suas imagens | Tudo |
| `system_events` | 403 | Acesso total |
| `users` | Sem acesso | Criar e listar |

### Seed do admin

No startup, o backend cria automaticamente o usuário definido em `ADMIN_USERNAME` / `ADMIN_PASSWORD` com role `superadmin`, caso não exista.

---

## Endpoints

Todos os endpoints estão sob `/api/v1`. A documentação interativa completa está disponível em `/docs` (Swagger UI) ou no arquivo [`../openapi.json`](../openapi.json).

### Públicos

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/` | Health check |
| `POST` | `/api/v1/auth/login` | Obter token JWT |

### Protegidos (requerem Bearer token)

| Recurso | Prefixo |
|---------|---------|
| Usuários | `/api/v1/users` |
| Plantas | `/api/v1/plants` |
| Dispositivos | `/api/v1/devices` |
| Leituras de sensor | `/api/v1/sensor-readings` |
| Eventos de irrigação | `/api/v1/irrigation-events` |
| Imagens | `/api/v1/images` |
| Análises de visão | `/api/v1/vision-analyses` |
| Eventos do sistema | `/api/v1/system-events` |
| Alertas | `/api/v1/alerts` |
| Plantação (início de ciclo) | `/api/v1/planting` |

---

## Variáveis de Ambiente

```env
# PostgreSQL
PGHOST=postgres
PGDATABASE=stovedb
PGUSER=stove
PGPASSWORD=<senha>
PGSSLMODE=disable
PGCHANNELBINDING=disable

# MQTT
MQTT_HOST=<cluster>.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USER=<usuario>
MQTT_PASSWORD=<senha>
MQTT_USE_TLS=true
MQTT_CLIENT_ID=gaia-backend
MQTT_TOPIC_PREFIX=gaia

# JWT
SECRET_KEY=<chave-aleatoria-min-32-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<senha-forte>
```

---

## Execução local

### Com Docker (recomendado)

```bash
# Na raiz do projeto
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend
```

### Sem Docker

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
python run.py
```

A API fica disponível em `http://localhost:8000`. Swagger em `http://localhost:8000/docs`.

---

## Schema do Banco

O arquivo `SQL/schema.sql` é executado automaticamente no startup se as tabelas não existirem. O bootstrap é idempotente — seguro para reinicializações.

### Tabelas

| Tabela | Descrição |
|--------|-----------|
| `users` | Usuários da aplicação (com `role`) |
| `plant` | Espécies de plantas (com `user_id`, faixa ideal incluindo `optimal_light_min/max`) |
| `device` | Dispositivos ESP32 vinculados a plantas |
| `sensor_reading` | Leituras de temperatura, umidade, solo, luz (`device_id` nullable; armazena também `light_percent`, `pump_state`, `stabilized`, `firmware_ts` vindos do `planta/status`) |
| `irrigation_event` | Acionamentos da bomba de irrigação |
| `plant_image` | Metadados de imagens capturadas |
| `vision_analysis` | Resultados de inferência ML |
| `system_event` | Auditoria de eventos do sistema |
| `alert` | Alertas gerados por leituras fora da faixa |
| `planta_estufa` | Ciclo de plantação em curso (`plant_id`, `life_days`, `dia_inclusao`, `dia_saida`, `dia_nascenca`) |
| `planta_alerta` | Alertas broadcast vindos do tópico `planta/alerta` (sem vínculo a `device`) |

---

## Lógica de Negócio

- **Status calculado** em `sensor_reading`: cada leitura é classificada como `normal`/`warning`/`critical` comparando com os parâmetros ideais da planta vinculada via `device.plant_id`.
- **Geração automática de alertas**: cada métrica fora da faixa ideal cria um registro em `alert`.
- **Heartbeat de dispositivo**: atualiza `device.last_seen_at` via MQTT ou endpoint `/heartbeat`.
- **Vínculo bidirecional** entre `plant_image` e `vision_analysis`: ao criar uma análise, `analysis_id` da imagem é preenchido automaticamente.

---

## Integração MQTT

O broker HiveMQ Cloud é conectado no startup. Tópicos utilizados:

| Tópico | Direção | Ação |
|--------|---------|------|
| `gaia/{device_id}/telemetry` | ESP32 → backend | Registra leitura de sensor |
| `gaia/{device_id}/heartbeat` | ESP32 → backend | Atualiza `last_seen_at` |
| `gaia/{device_id}/cmd/pump` | backend → ESP32 | Aciona bomba remotamente |
| `planta/config` | backend → ESP32 | Publica a planta recém-plantada (faixa ideal + `vida_dias`) |
| `planta/status` | ESP32 → backend | Telemetria broadcast do ciclo de rotina (sem `device_id`) |
| `planta/alerta` | ESP32 → backend | Lista de alertas broadcast do ciclo de rotina |

---

## Ciclos de operação

### Ciclo de Plantação

1. **App de Visão Computacional** identifica a espécie e chama `POST /api/v1/planting/start` com `{ "plant_name", "life_days" }`.
2. O backend localiza a planta em `plant` pelo `common_name` e cria uma linha em `planta_estufa` (`dia_inclusao = now()`).
3. Publica em MQTT `planta/config` o payload consumido pelo ESP interno:

   ```json
   {
     "nome": "Manjericão",
     "vida_dias": 30,
     "solo_min": 40.0, "solo_max": 70.0,
     "ar_umi_min": 50.0, "ar_umi_max": 80.0,
     "temp_min": 18.0, "temp_max": 28.0,
     "luz_min": 300.0, "luz_max": 1200.0
   }
   ```

### Ciclo de Rotina

O ESP interno publica periodicamente:

- `planta/status` — leitura completa (`ar_temp`, `ar_umi`, `solo_umi`, `luz_bruta`, `luz_pct`, `bomba`, `estabilizado`, `ts`); o backend grava em `sensor_reading` com `device_id = NULL`.
- `planta/alerta` — `{ "planta", "alertas": [{ "tipo", "nivel", "mensagem", "valor", "minimo" }, ...] }`; cada item vira uma linha em `planta_alerta`.

---

## Testes

### Fluxo ponta a ponta (in-process, mocka os aparelhos externos)

```bash
cd backend
python scripts/test_full_flow.py
```

O script mocka os 3 aparelhos externos (App de Visão, ESP-CAM, ESP interno),
exercita os ciclos de plantação e rotina contra o Postgres real definido no
`.env`, valida cada linha persistida e o payload publicado em `planta/config`,
e faz cleanup ao final.
