#!/usr/bin/env bash
# Deploy: build + start + logs em tempo real.
# Uso: bash scripts/deploy.sh [--with-ml]
set -euo pipefail

PROFILE_ARGS=""
if [[ "${1:-}" == "--with-ml" ]]; then
  PROFILE_ARGS="--profile ml"
fi

cd "$(dirname "$0")/.."

echo "==> Derrubando containers antigos..."
docker compose $PROFILE_ARGS down --remove-orphans

echo ""
echo "==> Build e subida dos serviços..."
docker compose $PROFILE_ARGS up --build -d

echo ""
echo "==> Aguardando serviços ficarem saudáveis..."
docker compose $PROFILE_ARGS ps

echo ""
echo "==> Logs (Ctrl+C para sair — os containers continuam rodando):"
docker compose $PROFILE_ARGS logs --follow --timestamps
