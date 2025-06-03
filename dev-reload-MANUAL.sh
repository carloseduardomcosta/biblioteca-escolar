#!/usr/bin/env bash
set -e

# Se quiser limpar volumes persistentes de dados (bancos, grafana, etc),
# descomente a linha abaixo:
# docker-compose down --volumes

# Desliga todos os containers do compose
docker-compose down

# Rebuilda as imagens e sobe tudo em segundo plano
docker-compose up -d --build

echo "✅  Docker containers rebuildados e reiniciados."
