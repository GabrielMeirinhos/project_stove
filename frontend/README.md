# Frontend — Gaia Monitoring Dashboard

Dashboard de monitoramento de estufa em tempo real com visualização procedural de plantas, métricas ambientais, histórico de crescimento e análise de imagens via ML.

---

## Stack

- **React 19** + **TypeScript**
- **Vite** — bundler (build de produção)
- **Express** — servidor Node.js que serve o app e integra MQTT/SSE
- **Tailwind CSS** — estilização
- **Recharts** — gráficos
- **React Three Fiber / Three.js** — visualização 3D procedural
- **Framer Motion** — animações
- **@google/genai** — integração Gemini (feature futura)

---

## Arquitetura

O frontend roda como um **servidor Express** que:

1. Em desenvolvimento: serve o app via middleware Vite (hot-reload)
2. Em produção: serve os arquivos estáticos buildados em `dist/`
3. Conecta ao broker MQTT e expõe dados de sensor via **SSE** (`/api/live/stream`)
4. Faz proxy de análise de imagem para o serviço de ML

O React consome APIs do próprio servidor Express (`/api/...`) — não há chamada direta do browser ao backend Python, exceto `getHistory()` que usa `VITE_BACKEND_URL`.

---

## Execução local

### Com Docker (recomendado)

```bash
# Na raiz do projeto
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend
```

O container usa hot-reload via volume mount. Disponível em `http://localhost:3000`.

### Sem Docker

```bash
cd frontend
npm install
npm run dev
```

### Outros comandos

```bash
npm run build      # build de produção
npm run preview    # preview do build
npm run lint       # lint TypeScript
```

---

## Variáveis de Ambiente

O frontend lê variáveis do `.env` na raiz do diretório `frontend/` (para desenvolvimento local sem Docker) ou do `.env` na raiz do projeto (via Docker Compose).

| Variável | Onde é usada | Observação |
|----------|-------------|------------|
| `GEMINI_API_KEY` | Build-time (Vite) | Embutida no bundle pelo Vite — deve ser passada como build arg no Docker |
| `MQTT_HOST` | Runtime (server.ts) | Host do broker HiveMQ |
| `MQTT_PORT` | Runtime (server.ts) | Padrão: `8883` |
| `MQTT_USER` | Runtime (server.ts) | |
| `MQTT_PASSWORD` | Runtime (server.ts) | |
| `MQTT_USE_TLS` | Runtime (server.ts) | Padrão: `true` |
| `MQTT_TOPIC_PREFIX` | Runtime (server.ts) | Padrão: `gaia` |
| `ML_INFERENCE_URL` | Runtime (server.ts) | Padrão: `http://ml-inference:8001` |
| `NODE_ENV` | Runtime | `production` no Docker |

> **Atenção:** `GEMINI_API_KEY` é injetada pelo Vite **em tempo de build** via `vite.config.ts`. No Docker, ela é passada como `build arg` — não basta definir apenas no `environment` do compose.

---

## APIs do Servidor Express

O `server.ts` expõe as seguintes rotas:

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/dados` | Última leitura de sensor recebida via MQTT |
| `GET` | `/api/mqtt/status` | Status da conexão com o broker |
| `GET` | `/api/live/stream` | Stream SSE com dados em tempo real |
| `GET` | `/api/modelo-atual?day=N` | Metadados do modelo 3D para o dia N |
| `GET` | `/api/historico` | Histórico simulado de crescimento |
| `POST` | `/api/analyze-image` | Proxy para o serviço ML de análise de imagem |

---

## Integração com o Backend Python

O serviço `src/services/api.ts` consome o backend Python diretamente para histórico de sensor:

```typescript
const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000/api/v1';
```

O backend exige **token JWT** em todas as rotas protegidas. Para integração completa, o frontend precisará implementar um fluxo de login que obtenha e armazene o token via `POST /api/v1/auth/login`.

---

## Estrutura

```
frontend/
├── src/
│   ├── App.tsx                    # Navegação entre módulos
│   ├── components/
│   │   ├── dashboard/             # Blocos visuais do painel
│   │   ├── layout/                # Sidebar e navegação
│   │   └── ui/                    # Componentes reutilizáveis
│   ├── services/
│   │   └── api.ts                 # Client HTTP para o backend Python
│   └── types/                     # Tipos TypeScript compartilhados
├── server.ts                      # Servidor Express + MQTT + SSE
├── vite.config.ts                 # Config Vite (injeta GEMINI_API_KEY no build)
├── Dockerfile                     # Multi-stage: deps → builder → runner
└── .env.example
```

---

## Docker

O `Dockerfile` usa build multi-stage:

| Stage | Descrição |
|-------|-----------|
| `deps` | Instala dependências npm |
| `builder` | Roda `npm run build` com `GEMINI_API_KEY` como `ARG` |
| `runner` | Serve o app com `tsx server.ts` em produção |

O `docker-compose.override.yml` (aplicado automaticamente em dev) monta o código como volume e usa o stage `deps` com `npm run dev`.
