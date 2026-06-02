# Backend Isolado de Autenticacao (Gaia)

Este modulo foi criado dentro de `backend/auth_isolated` sem alterar os arquivos existentes do backend principal.

## Objetivo
- Login real
- Perfis `admin` e `user`
- Convite por link
- Reset de senha por link
- Endpoints administrativos isolados

## Estrutura
- `app/main.py`: API FastAPI isolada
- `app/security.py`: hash de senha e token assinado
- `app/store.py`: acesso ao SQLite local do modulo
- `app/db.py`: schema e inicializacao do banco
- `.env.example`: variaveis de ambiente

## Como rodar
```bash
cd backend/auth_isolated
python -m uvicorn app.main:app --reload --port 8005
```

## Banco local
Por padrao, usa `backend/auth_isolated/data/auth.sqlite3`.

## Importante
Este modulo nao foi acoplado ao backend principal para evitar conflito com o trabalho dos outros colaboradores.
