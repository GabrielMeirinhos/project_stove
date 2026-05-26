# Relatório de Reorganização — Stove Project

**Data**: 2026-05-25
**Executado por**: Claude Code (claude-sonnet-4-6)

---

## 1. Estrutura Antiga vs Nova

### Antes

```
project_stove/
├── .env                           ⚠️  credenciais raiz (já desrastreado)
├── .gitignore
├── README.md                      ℹ️  só documentava o ML
├── main.py                        ← download do dataset (raiz)
├── plant_classification_pipeline.py ← ML pipeline (raiz)
├── requirements.txt               ← dependências Python na raiz
├── venv/                          ← venv na raiz (gitignored)
├── outputs/                       ← artefatos ML na raiz
├── backend/
│   ├── .env.example
│   ├── .claude/settings.local.json
│   ├── requirements.txt
│   ├── run.py
│   ├── SQL/
│   ├── docs/
│   ├── scripts/
│   └── app/
└── front/                         ← nome inconsistente
    ├── .env.example
    ├── .gitignore                 ← gitignore separado do frontend
    ├── package.json
    └── src/
```

### Depois

```
project_stove/
├── .env.example                   ✅ unificado com todas as vars
├── .gitignore                     ✅ unificado e atualizado
├── README.md                      ✅ overview completo do projeto
├── pyproject.toml                 ✅ config ruff + pyright
├── .pre-commit-config.yaml        ✅ hooks automáticos
├── docker-compose.yml             ✅ dev + serviços completos
├── docker-compose.override.yml    ✅ hot-reload dev
├── docker-compose.prod.yml        ✅ produção
├── MIGRATION_REPORT.md            ✅ este arquivo
├── .github/
│   └── workflows/
│       └── ci.yml                 ✅ CI para backend, frontend e ml
├── docs/
│   ├── architecture.md            ✅ arquitetura completa + diagrama
│   ├── setup.md                   ✅ setup local passo a passo
│   ├── docker.md                  ✅ guia Docker dev/prod
│   └── ml.md                      ✅ guia ML + treinamento + deploy RPi
├── frontend/                      ✅ renomeado de front/
│   ├── Dockerfile                 ✅ multi-stage (deps → builder → runner)
│   ├── .dockerignore              ✅
│   └── [código existente]
├── backend/
│   ├── Dockerfile                 ✅
│   ├── .dockerignore              ✅
│   └── [código existente]
├── ml/                            ✅ novo módulo isolado
│   ├── Dockerfile                 ✅ com suporte a OpenCV nativo
│   ├── .dockerignore              ✅
│   ├── requirements.txt           ✅ movido da raiz
│   ├── __init__.py
│   ├── datasets/                  (gitignored)
│   ├── models/                    (gitignored)
│   ├── checkpoints/               (gitignored)
│   ├── outputs/
│   ├── notebooks/
│   ├── experiments/
│   ├── training/
│   │   ├── __init__.py
│   │   ├── pipeline.py            ✅ movido de plant_classification_pipeline.py
│   │   └── download_dataset.py   ✅ movido de main.py
│   └── inference/
│       └── __init__.py
├── infra/                         ✅ (placeholder para k8s/terraform)
└── scripts/                       ✅ (placeholder para scripts compartilhados)
```

---

## 2. Mudanças Realizadas

### Estrutura e Organização

| Ação | Detalhe |
|------|---------|
| Renomeado | `front/` → `frontend/` (via `git mv`, histórico preservado) |
| Movido | `plant_classification_pipeline.py` → `ml/training/pipeline.py` |
| Movido | `main.py` → `ml/training/download_dataset.py` |
| Movido | `requirements.txt` (raiz) → `ml/requirements.txt` |
| Criado | `ml/` com subdirs: datasets, models, checkpoints, notebooks, training, inference, experiments, outputs |
| Criado | `docs/`, `infra/`, `scripts/` |

### .gitignore

- Unificado: `front/.gitignore` absorvido pelo root `.gitignore`
- Adicionados: paths do módulo `ml/` (datasets, models, checkpoints)
- Adicionados: `node_modules/`, `frontend/dist/`, `*.tsbuildinfo`
- Adicionada: regra `!.env.example` para garantir que o exemplo seja sempre commitável

### Docker

| Arquivo | Descrição |
|---------|-----------|
| `frontend/Dockerfile` | Multi-stage: `deps` → `builder` → `runner`. Imagem final ~200MB |
| `backend/Dockerfile` | Python 3.12-slim, sem camadas desnecessárias |
| `ml/Dockerfile` | Python 3.12-slim + libgl1 + libglib2.0-0 (OpenCV nativo) |
| `docker-compose.yml` | Frontend + Backend + ML (profile) com healthcheck e volumes |
| `docker-compose.override.yml` | Dev: volume mounts + hot-reload |
| `docker-compose.prod.yml` | Prod: imagens baked, restart=always |

### CI/CD

- `.github/workflows/ci.yml` criado com 4 jobs: `backend`, `frontend`, `ml`, `docker`
- Backend: ruff lint + pyright type check
- Frontend: TypeScript type check (`tsc --noEmit`) + Vite build
- ML: ruff lint
- Docker: build validation das 3 imagens

### Qualidade

| Arquivo | Descrição |
|---------|-----------|
| `pyproject.toml` | ruff (lint + format) + pyright config |
| `.pre-commit-config.yaml` | trailing whitespace, YAML/JSON check, detect-private-key, ruff, tsc, detect-secrets |

---

## 3. Riscos Encontrados

### 🔴 Crítico — Credenciais no histórico Git

O commit `e6275c6` removeu o `.env` do tracking, mas as credenciais (Neon DB password, HiveMQ password) ainda existem no histórico Git.

**Ação necessária imediata:**
1. Revogar e regenerar todas as credenciais expostas (Neon, HiveMQ, Gemini)
2. Limpar o histórico com `git filter-repo`:
   ```bash
   pip install git-filter-repo
   git filter-repo --path .env --invert-paths --force
   git push --force-with-lease origin main
   ```
3. Forçar todos os colaboradores a fazer `git fetch --all && git reset --hard origin/main`

### 🟡 Alto — CORS aberto em produção

`backend/app/main.py` tem `allow_origins=["*"]`. Em produção, restringir para o domínio real do frontend.

### 🟡 Alto — Frontend sem health endpoint no backend

O `docker-compose.yml` usa `/api/v1/plants` como health check do backend. Recomendado adicionar um endpoint `/health` dedicado no FastAPI.

### 🟡 Médio — `npm start` não funciona para TypeScript

`package.json` tem `"start": "node server.ts"` que falha pois `node` não processa TypeScript. Deve ser `tsx server.ts` ou compilar primeiro. O Dockerfile já usa `tsx`, mas o script de produção está incorreto.

### 🟠 Médio — Morango sub-representado no dataset ML

O PlantVillage tem poucos exemplos de morango. Predições para morango serão menos confiáveis até coleta de dados complementares.

### 🟠 Médio — `backend/.claude/settings.local.json` não deve ser commitado

Arquivo de configuração local do Claude Code incluso no repositório. Já adicionado ao `.gitignore` agora.

---

## 4. Pendências Técnicas

### Curto prazo (antes do próximo deploy)

- [ ] Revogar credenciais expostas no histórico e limpar com `git filter-repo`
- [ ] Restringir CORS para domínio específico em produção
- [ ] Corrigir script `npm start` no `frontend/package.json` (usar `tsx`)
- [ ] Adicionar endpoint `/health` no backend FastAPI
- [ ] Instalar pre-commit: `pip install pre-commit && pre-commit install`

### Médio prazo

- [ ] Criar módulo `ml/inference/classifier.py` (wrapper standalone do modelo TFLite)
- [ ] Integrar inferência ML com endpoint `POST /api/v1/vision/analyze` no backend
- [ ] Coletar mais imagens de morango para balancear dataset
- [ ] Adicionar testes unitários (pytest no backend, vitest no frontend)
- [ ] Configurar `detect-secrets`: `detect-secrets scan > .secrets.baseline`
- [ ] Remover `backend/.claude/settings.local.json` do tracking: `git rm --cached backend/.claude/settings.local.json`

### Longo prazo

- [ ] Fine-tuning com fotos de celular (domínio diferente do PlantVillage)
- [ ] Deploy no Raspberry Pi com TFLite runtime
- [ ] Infra como código em `infra/` (Docker Swarm ou k8s leve)
- [ ] CD pipeline para deploy automático

---

## 5. Como Iniciar Após a Reorganização

```bash
# 1. Instalar pre-commit
pip install pre-commit
pre-commit install

# 2. Configurar ambiente
cp .env.example .env
# edite .env

# 3. Subir via Docker
docker compose up --build

# --- OU ---

# 3. Desenvolvimento sem Docker
cd backend && pip install -r requirements.txt && python run.py
cd frontend && npm install && npm run dev
```
