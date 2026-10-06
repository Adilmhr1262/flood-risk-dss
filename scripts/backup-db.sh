#!/usr/bin/env bash
# FloodSafe Pakistan — PostgreSQL backup with rotation.
#
# Usage:
#   scripts/backup-db.sh                 # backup to database/backups/
#   BACKUP_DIR=/var/backups/floodsafe scripts/backup-db.sh
#   RETENTION_DAYS=30 scripts/backup-db.sh
#
# Connection comes from the backend DATABASE_URL (same parsing the app
# uses). The dump is a custom-format pg_dump (-Fc) named
# flood_risk_dss-YYYY-MM-DD_HHMM.dump. Files older than RETENTION_DAYS
# (default 14) are deleted. Restore with:
#   pg_restore -d <database> --clean database/backups/<file>.dump
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../database/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
mkdir -p "$BACKUP_DIR"

# Read DATABASE_URL from backend/.env (same value the app boots with).
ENV_FILE="$(dirname "$0")/../backend/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found" >&2
  exit 1
fi
DATABASE_URL="$(grep -E '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)"

# Split postgresql://user:password@host:port/dbname (or socket variant).
if [[ "$DATABASE_URL" =~ postgresql(\+psycopg2)?://([^:]+):([^@]+)@([^/]+)/(.+) ]]; then
  DB_USER="${BASH_REMATCH[2]}"
  export PGPASSWORD="${BASH_REMATCH[3]}"
  HOSTPORT="${BASH_REMATCH[4]}"
  DB_NAME="${BASH_REMATCH[5]}"
  DB_HOST="${HOSTPORT%%:*}"
  DB_PORT="${HOSTPORT##*:}"
  [ "$DB_HOST" = "$DB_PORT" ] && DB_PORT="5432"
  CONN_ARGS=(-h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME")
else
  echo "ERROR: could not parse DATABASE_URL" >&2
  exit 1
fi

STAMP="$(date +%Y-%m-%d_%H%M)"
OUT="$BACKUP_DIR/flood_risk_dss-${STAMP}.dump"

pg_dump -Fc "${CONN_ARGS[@]}" -f "$OUT"
echo "backup written: $OUT ($(du -h "$OUT" | cut -f1))"

# Rotation.
DELETED="$(find "$BACKUP_DIR" -name 'flood_risk_dss-*.dump' -mtime "+$RETENTION_DAYS" -print -delete | wc -l)"
echo "rotation: removed $DELETED backup(s) older than $RETENTION_DAYS days"

# Sanity: the newest dump restores the schema (list-only check).
pg_restore -l "$OUT" > /dev/null && echo "dump integrity check: OK"
