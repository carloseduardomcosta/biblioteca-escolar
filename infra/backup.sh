#!/bin/bash
# Backup semanal do biblioteca-escolar (banco MySQL + barcodes gerados)
# Retenção: 90 dias
# Cron: 15 4 * * 0 /opt/clientes/saas/biblioteca-escolar/infra/backup.sh

set -euo pipefail

PROJECT_DIR="/opt/clientes/saas/biblioteca-escolar"
BACKUP_DIR="$PROJECT_DIR/backups"
BARCODES_DIR="$PROJECT_DIR/app/static/barcodes"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=90

mkdir -p "$BACKUP_DIR"

# ── Banco de dados ────────────────────────────────────────────────────────────
if docker ps --filter "name=biblioteca-db" --filter "status=running" -q | grep -q .; then
  docker exec biblioteca-db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers "$MYSQL_DATABASE"' \
    | gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"
  echo "$(date): ✅ Backup do banco → db_${DATE}.sql.gz"
else
  echo "$(date): ⚠️  biblioteca-db não está rodando — backup do banco pulado"
fi

# ── Barcodes gerados (não versionados no git) ─────────────────────────────────
if [ -d "$BARCODES_DIR" ] && [ "$(ls -A "$BARCODES_DIR" 2>/dev/null)" ]; then
  tar -czf "$BACKUP_DIR/barcodes_${DATE}.tar.gz" -C "$(dirname "$BARCODES_DIR")" "$(basename "$BARCODES_DIR")"
  echo "$(date): ✅ Backup dos barcodes → barcodes_${DATE}.tar.gz"
fi

# ── Limpeza: remove backups mais antigos que a retenção ───────────────────────
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "barcodes_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
echo "$(date): 🧹 Limpeza: removidos backups > ${RETENTION_DAYS} dias"
