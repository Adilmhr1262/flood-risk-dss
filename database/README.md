# Database Layer — Flood Risk Prediction and Early Warning Decision Support System

PostgreSQL 15 + PostGIS schema and seed data for Pakistan (Sindh focus, southern Punjab).

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Full DDL: enums, tables, triggers, spatial indexes, `v_latest_predictions` view |
| `seed.sql` | Demo users, 12 assessment points, 52 historical flood events, 6 shelters, 8 emergency contacts, 4 sample predictions, 3 active alerts |

## Setup

### 1. Install prerequisites

```bash
# Debian/Ubuntu
sudo apt install postgresql-15 postgresql-15-postgis-3
```

PostGIS is required — `geographic_data.geom` and `shelters.geom` are `GEOMETRY(Point, 4326)` columns with GIST spatial indexes.

### 2. Create the database

```bash
sudo -u postgres createdb flood_risk_dss
sudo -u postgres createuser -P floodapp        # set a password
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE flood_risk_dss TO floodapp;"
```

### 3. Apply schema, then seed

```bash
psql -h localhost -U floodapp -d flood_risk_dss -f database/schema.sql
psql -h localhost -U floodapp -d flood_risk_dss -f database/seed.sql
```

Both scripts are re-runnable: `schema.sql` uses `CREATE ... IF NOT EXISTS` guards
for tables, indexes, and the `user_role` enum, and `DROP TRIGGER IF EXISTS` before
recreating triggers.

### 4. Verify

```bash
psql -h localhost -U floodapp -d flood_risk_dss -c "SELECT count(*) FROM flood_events;"
# → 52

psql -h localhost -U floodapp -d flood_risk_dss -c "SELECT district_name, risk_level, probability FROM v_latest_predictions;"
```

## Table Summary

| Table | Description | Key columns |
|---|---|---|
| `users` | App users with role-based access | `role` ∈ authority / ngo / public |
| `geographic_data` | District assessment points (topography + social vulnerability) | `geom` (PostGIS Point 4326), `elevation_m`, `river_distance_km`, `vulnerability_index` 0–1 |
| `flood_events` | Historical flood records (model training / trend analysis) | `event_date`, `severity` 1–5, `rainfall_mm`, `affected_population` |
| `weather_observations` | Time-series weather records per district | `observed_at`, `rainfall_mm`, `temperature_c`, `humidity_pct`; UNIQUE(`geographic_id`, `observed_at`, `source`) |
| `district_boundaries` | District boundary polygons for GIS layers | `geom` (PostGIS MultiPolygon 4326), one row per district |
| `predictions` | Machine learning-based risk outputs | `probability` 0–1, `risk_level` LOW/MEDIUM/HIGH, `input_features` JSONB, `main_factors`/`recommendations` arrays |
| `alerts` | Early-warning alerts | `severity` info/watch/warning/emergency, `is_active` |
| `shelters` | Emergency shelters / relief centres | `geom`, `capacity`, `facilities` array |
| `emergency_contacts` | Rescue & relief contact directory | `organization`, `phone`, `district_name` |

## Design notes

- **PostGIS:** spatial GIST indexes on `geographic_data.geom`, `shelters.geom`,
  and `district_boundaries.geom` support map-layer queries and nearest-shelter
  lookups (e.g. `ST_DWithin`, `ST_Distance`).
- **`updated_at` triggers:** `set_updated_at()` keeps `updated_at` current on every
  mutable table (`users`, `geographic_data`, `flood_events`, `shelters`,
  `emergency_contacts`, `district_boundaries`).
- **`predictions` is append-only** (no update trigger) — each prediction run is a
  new row; `v_latest_predictions` returns the newest prediction per location.
- **Check constraints** enforce domain ranges: probability 0–1, risk level enum,
  severity 1–5, latitude/longitude bounds, non-negative distances and capacities.
- **Seed data** references real history (2010 super floods, 2011 Sindh floods,
  2020 Karachi urban flooding, 2022 Pakistan floods) with approximate real
  district-centre coordinates for Sindh and southern Punjab.

## Migrations (Alembic)

The canonical schema lives in `database/schema.sql`; Alembic migrations in
`backend/alembic/` track every schema change for repeatable deployments.

```bash
cd backend

# Apply all migrations to the configured database
DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db" \
  .venv/bin/alembic upgrade head

# Preview the SQL without connecting
DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db" \
  .venv/bin/alembic upgrade head --sql

# Roll back one revision (or all the way: `downgrade base`)
.venv/bin/alembic downgrade -1
```

Migration history:

| Revision | Description |
|---|---|
| `0001` | Baseline reproducing `database/schema.sql` exactly (7 tables, `user_role` enum, triggers, indexes, `v_latest_predictions` view) |
| `0002` | `weather_observations` + `district_boundaries` tables |

### Creating a new migration

```bash
cd backend
.venv/bin/alembic revision -m "add reservoir_levels table"
# edit backend/alembic/versions/<rev>_add_reservoir_levels_table.py
.venv/bin/alembic upgrade head
```

Guidelines:

- Keep `database/schema.sql` and the migration chain in sync: schema.sql is the
  human-readable source of truth; migrations are the deployment mechanism.
- Prefer `op.create_table` / `op.add_column` for new objects; use `op.execute`
  for PostGIS DDL, triggers, and views (as in `0001`).
- geoalchemy2 `Geometry` columns auto-create a spatial index by default — pass
  `spatial_index=False` in migrations when creating the GIST index explicitly
  (see `0002`).
- Always verify a new migration: apply it to an empty database and diff
  `information_schema.columns` against the reference database.

## Demo logins (seed)

| Role | Email | Password |
|---|---|---|
| Authority | `authority.demo@flooddss.pk` | *(placeholder hash — set a real bcrypt hash)* |
| NGO | `ngo.demo@flooddss.pk` | *(placeholder hash — set a real bcrypt hash)* |
| Public | `public.demo@flooddss.pk` | *(placeholder hash — set a real bcrypt hash)* |

> The seed uses `$2b$12$DEMO_HASH_PLACEHOLDER` as `password_hash`. Replace with real
> bcrypt hashes before any deployment.
