#!/usr/bin/env bash
# FloodSafe Pakistan — reset the demo environment.
#
# Deletes operational rows typically created during a live demo
# (incidents, notes, response teams, citizen reports, alerts) so the next
# demo starts clean. Reference/seed data (districts, shelters, emergency
# contacts, flood history, users, weather, predictions) is NOT touched.
#
# Usage: scripts/demo-reset.sh
set -euo pipefail

ENV_FILE="$(dirname "$0")/../backend/.env"
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found" >&2; exit 1; }
DATABASE_URL="$(grep -E '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)"

echo "This will DELETE all rows from:"
echo "  incident_notes, incidents, response_teams, citizen_reports, alerts"
echo "in the database from DATABASE_URL."
read -r -p "Type RESET to confirm: " CONFIRM
[ "$CONFIRM" = "RESET" ] || { echo "aborted"; exit 0; }

psql "$DATABASE_URL" <<'EOF'
-- No child tables reference these (FKs point to geographic_data/users),
-- so a plain TRUNCATE is safe and cannot cascade into seed data.
TRUNCATE incident_notes, incidents, response_teams, citizen_reports, alerts RESTART IDENTITY;
EOF
echo "demo environment reset complete"
