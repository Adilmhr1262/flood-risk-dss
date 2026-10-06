#!/usr/bin/env bash
# Rebuild the Flood Risk DSS PostgreSQL databases from project sources.
#
# Use when the local PostgreSQL cluster has been reset (this has happened
# more than once in this sandbox: only postgres/template* databases remain).
#
# Order matters: migration 0001 -> seed.sql -> migrations 0002-0005,
# because data migrations in 0003+ expect the seeded districts.
#
# Usage: ./scripts/rebuild-db.sh
# Requires: running postgres cluster, backend/.venv, backend/.env

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

PW="$(grep -oP '(?<=flood_dss:)[^@]+' .env | head -1)"
if [ -z "$PW" ]; then
  echo "Could not read flood_dss password from backend/.env" >&2
  exit 1
fi

echo "==> Ensuring role and databases exist"
su postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='flood_dss'\" | grep -q 1 || psql -c \"CREATE ROLE flood_dss WITH LOGIN PASSWORD '$PW';\""
for db in flood_risk_dss flood_risk_dss_test; do
  su postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='$db'\" | grep -q 1 || psql -c 'CREATE DATABASE $db OWNER flood_dss;'"
  su postgres -c "psql -d $db -c 'CREATE EXTENSION IF NOT EXISTS postgis;'"
done

echo "==> Alembic migration 0001 (schema baseline)"
.venv/bin/alembic upgrade 0001

echo "==> Loading database/seed.sql"
PGPASSWORD="$PW" psql -h 127.0.0.1 -U flood_dss -d flood_risk_dss -q -f "$ROOT/database/seed.sql"

echo "==> Alembic migrations 0002-0005"
.venv/bin/alembic upgrade head

echo "==> Verification"
PGPASSWORD="$PW" psql -h 127.0.0.1 -U flood_dss -d flood_risk_dss -c \
  "select 'districts', count(*) from geographic_data union all select 'events', count(*) from flood_events union all select 'users', count(*) from users;"

echo "Done. Restart the API server before use."
