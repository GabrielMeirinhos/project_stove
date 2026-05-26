# Setup Local — Desenvolvimento sem Docker

## Pré-requisitos

| Ferramenta | Versão mínima |
|-----------|---------------|
| Python | 3.12 |
| Node.js | 22 |
| npm | 10 |
| Git | 2.40 |

## 1. Clone e configuração inicial

```bash
git clone <repo-url>
cd project_stove

# Copie e edite as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais (Neon, HiveMQ, Gemini, Kaggle)
```

## 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

# Inicia na porta 8000
python run.py
```

API disponível em: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

## 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard disponível em: `http://localhost:3000`

## 4. ML (treinamento)

```bash
cd ml
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows

pip install -r requirements.txt

# Baixa dataset PlantVillage do Kaggle (requer KAGGLE_USERNAME e KAGGLE_KEY no .env)
python training/download_dataset.py

# Treina o modelo (fase 1 + fase 2 + exportação TFLite)
python training/pipeline.py
```

## 5. Simulador ESP32 (mock)

```bash
# Backend mock (Python)
cd backend
python scripts/mock_esp32.py

# Frontend mock (MQTT)
cd frontend
npm run mqtt:sim
```

## Variáveis de ambiente

Ver [`.env.example`](../.env.example) para a lista completa com descrições.

## Solução de problemas

**Erro de conexão PostgreSQL**: verifique `PGHOST`, `PGPASSWORD` e certifique que `PGSSLMODE=require`.

**Backend não inicia**: o schema do banco é criado automaticamente no startup (`app/db/schema.py`).

**Frontend 3D não renderiza**: verifique se o browser suporta WebGL (`about:gpu` no Chrome).
