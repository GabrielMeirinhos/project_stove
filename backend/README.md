# Sistema de Monitoramento de Horta Inteligente — Backend Python

Backend em **Python + FastAPI** conectado a **PostgreSQL (Neon)** que
implementa o schema descrito em `documentacao_banco.pdf` (versão
1.0/2025). A documentação prevê Spring Boot como backend oficial; este
projeto entrega a **mesma especificação funcional** em Python, mantendo
intactos:

- as **8 entidades** descritas na seção 3 do PDF (`plant`, `device`,
  `sensor_reading`, `irrigation_event`, `plant_image`, `vision_analysis`,
  `system_event`, `alert`);
- todos os **relacionamentos** e **cardinalidades** da seção 4;
- as **decisões de design** da seção 6 (UUID como PK, status calculado,
  separação alerta/evento, etc.);
- as **convenções de nomenclatura** da seção 7;

## Estrutura

```
projeto_7_periodo/
├── README.md
├── requirements.txt
├── .env                     # credenciais Neon (PGHOST, PGUSER, ...)
├── run.py                   # entrypoint uvicorn
├── documentacao_banco.pdf   # documentação original
├── sql/
│   └── schema.sql           # schema PostgreSQL (executado no startup)
└── app/
  ├── main.py              # lifespan, registro de routers + CORS
  ├── config.py            # constantes + leitura do .env
  ├── database.py          # singletons de repositório por tabela
  ├── db/
  │   ├── connection.py    # pool psycopg-pool
  │   ├── repository.py    # PostgresRepository (CRUD genérico)
  │   └── schema.py        # bootstrap idempotente do schema
  ├── schemas/             # modelos Pydantic por entidade
  ├── services/            # regras de negócio
  └── routers/             # endpoints REST por entidade
```

## Persistência (Neon PostgreSQL)

A aplicação se conecta ao Neon usando as variáveis libpq padrão
(`PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGSSLMODE`,
`PGCHANNELBINDING`) carregadas do arquivo `.env`. No startup
(`lifespan` do FastAPI) o backend:

1. abre um pool de conexões (`psycopg_pool.ConnectionPool`);
2. verifica se a tabela `plant` existe; se não, executa
   `sql/schema.sql` (idempotente).

A camada de acesso a dados expõe um `PostgresRepository` genérico
(`app/db/repository.py`) com **a mesma interface** usada antes pelo
banco figurativo — isso significa que serviços e routers continuaram
funcionando sem qualquer alteração quando trocamos a persistência.

## Lógica de negócio implementada

- **Status calculado** em `sensor_reading` (seção 6.3): cada leitura é
  classificada como `normal`/`warning`/`critical` no momento da inserção,
  comparando os valores recebidos com os parâmetros ideais da planta
  vinculada via `device.plant_id`.
- **Geração automática de alertas** (seção 3.8): cada métrica fora da
  faixa ideal cria um registro em `alert` referenciando a leitura
  responsável pelo disparo.
- **Heartbeat de dispositivo** (seção 3.2): a chegada de uma leitura ou
  de uma chamada explícita ao endpoint `/heartbeat` atualiza
  `device.last_seen_at`.
- **Vínculo bidirecional** entre `plant_image` e `vision_analysis`
  (seção 4): ao criar uma análise, o `analysis_id` da imagem é
  preenchido automaticamente.
- **Resolução de alertas**: o endpoint dedicado preenche `resolved` e
  `resolved_at` (seção 6.5: alertas têm estado, eventos não).

## Como executar

```bash
# 1. (opcional) criar virtualenv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 2. instalar dependências
pip install -r requirements.txt

# 3. rodar a API
python run.py
```

A API ficará disponível em <http://localhost:8000>. A documentação
interativa Swagger está em <http://localhost:8000/docs> e a versão
ReDoc em <http://localhost:8000/redoc>.

Todos os endpoints são versionados sob `/api/v1`. Exemplo:

```
GET  /api/v1/plants
POST /api/v1/sensor-readings
GET  /api/v1/alerts?only_active=true
```

## Fluxo recomendado para apresentação

Conforme a seção 10 do PDF:

1. `POST /api/v1/plants` — cadastrar uma espécie com seus parâmetros
   ideais.
2. `POST /api/v1/devices` — cadastrar um ESP32 vinculado à planta.
3. `POST /api/v1/sensor-readings` — enviar uma leitura com valor fora
   da faixa configurada.
4. `GET /api/v1/sensor-readings` — observar o `status` calculado.
5. `GET /api/v1/alerts?only_active=true` — observar o alerta gerado
   automaticamente para a métrica violada.
6. `POST /api/v1/alerts/{id}/resolve` — resolver o alerta após
   normalização.

## Roadmap para produção

- adicionar autenticação/autorização (`OAuth2PasswordBearer`);
- consumir o broker MQTT em background (`asyncio-mqtt`/`paho-mqtt`)
  para receber leituras direto do ESP32;
- mover o conteúdo de `image_base64` para armazenamento externo
  (S3/GCS) e usar apenas `storage_path`, conforme seção 6.2;
- não versionar `.env` (mover credenciais para o segredos manager do
  ambiente de deploy).
