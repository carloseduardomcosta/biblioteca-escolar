#!/usr/bin/env bash
#
# dev-reload.sh
# Sempre que algum .py, .html, .env, Dockerfile ou
# compose mudar, derruba e sobe tudo de novo em background

# diretórios a observar (ajuste conforme seu layout)
WATCH_DIRS=(app mysql)

# padrões de arquivo
EXTENSIONS="\.py|\.html|\.env|Dockerfile|docker-compose\.yml$"

# timeout para não disparar mil rebuilds seguidos
DEBOUNCE_SEC=1

# checa se inotifywait está instalado
command -v inotifywait >/dev/null 2>&1 || {
  echo "Por favor instale inotify-tools (apt install inotify-tools)"
  exit 1
}

echo "👀  Observando alterações em: ${WATCH_DIRS[*]}"
while inotifywait -e modify,create,delete -r "${WATCH_DIRS[@]}" . |
      grep --line-buffered -E $EXTENSIONS
do
  echo "🛠️  Mudança detectada em $(date +'%H:%M:%S'), rebuild em ${DEBOUNCE_SEC}s…"
  sleep $DEBOUNCE_SEC

  echo "🔴 Parando stack…"
  docker compose down

  echo "🟢 Build & up em background…"
  docker compose up -d --build

  echo "✅ Pronto! Containers rodando em segundo plano."
done
