# Database Schema

PostgreSQL 15 + PostGIS. All primary keys are UUIDs (`gen_random_uuid()`).
Geometries use SRID 4326 (WGS 84). Timestamps are `TIMESTAMPTZ` (UTC).
DDL: `database/schema.sql` · Seed data: `database/seed.sql`.

## Tables

### users
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(150) | |
| email | VARCHAR(255) UNIQUE | login identifier |
| password_hash | VARCHAR(255) | bcrypt |
| role | user_role enum | `authority` / `ngo` / `public` / `volunteer` (0004) |
| location_name | VARCHAR(150) | user's district |
| phone | VARCHAR(30) | |
| created_at / updated_at | TIMESTAMPTZ | updated_at via trigger |

### geographic_data
Master location table — one row per district. All spatial analysis joins here.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| district_name | VARCHAR(150) | e.g. `Dadu` |
| province | VARCHAR(100) | e.g. `Sindh` |
| geom | GEOMETRY(Point, 4326) | district centroid, GIST-indexed |
| latitude / longitude | DOUBLE PRECISION | |
| elevation_m | DOUBLE PRECISION | metres above sea level |
| river_distance_km | DOUBLE PRECISION | distance to nearest major river (Indus) |
| slope_deg | DOUBLE PRECISION | average terrain slope |
| population_density_per_km2 | DOUBLE PRECISION | |
| vulnerability_index | DOUBLE PRECISION | composite social vulnerability, 0–1 |

### flood_events
Historical record. 52 seeded rows (2010 super floods, 2011 Sindh floods,
2022 Pakistan floods, 2020 Karachi, 2015/2019/2021/2023/2024).
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| geographic_id | UUID FK → geographic_data | ON DELETE CASCADE |
| event_date | DATE | indexed |
| rainfall_mm / temperature_c / humidity_pct | DOUBLE PRECISION | |
| severity | SMALLINT | 1 (minor) – 5 (catastrophic) |
| flood_status | BOOLEAN | |
| damage_description | TEXT | |
| affected_population | INTEGER | |
| source | VARCHAR(200) | e.g. `NDMA report` |

### predictions
Every risk assessment is persisted with its inputs for auditability.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| geographic_id | UUID FK → geographic_data | ON DELETE CASCADE |
| model_version | VARCHAR(50) | e.g. `rf-v1.2`, `v1.0.0-rule-based` |
| probability | DOUBLE PRECISION | 0–1, CHECK constrained |
| risk_level | VARCHAR(10) | `LOW` / `MEDIUM` / `HIGH` |
| input_features | JSONB | full input vector (GIN-indexed) |
| main_factors | TEXT[] | e.g. `{Heavy rainfall, Low elevation}` |
| recommendations | TEXT[] | action guidance per level |
| predicted_at | TIMESTAMPTZ | |
| created_by | UUID FK → users | ON DELETE SET NULL |

### alerts
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| geographic_id | UUID FK → geographic_data | ON DELETE CASCADE |
| title / message | VARCHAR(255) / TEXT | |
| severity | VARCHAR(20) | `info` / `watch` / `warning` / `emergency` |
| is_active | BOOLEAN | |
| issued_at / expires_at | TIMESTAMPTZ | |

### weather_observations *(migration 0002)*
Time-series weather records per district — feeds rainfall-trend charts and the
prediction service's environmental inputs.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| geographic_id | UUID FK → geographic_data | ON DELETE CASCADE |
| observed_at | TIMESTAMPTZ | indexed |
| rainfall_mm / temperature_c / humidity_pct | DOUBLE PRECISION | range-checked |
| source | VARCHAR(200) NOT NULL DEFAULT 'unknown' | NOT NULL so the natural-key UNIQUE is effective (NULLs never conflict) |
| created_at | TIMESTAMPTZ | |

UNIQUE(`geographic_id`, `observed_at`, `source`) — duplicate-safe bulk imports.

### district_boundaries *(migration 0002)*
One MultiPolygon boundary per district for GIS boundary/risk layer rendering.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| geographic_id | UUID FK → geographic_data, UNIQUE | ON DELETE CASCADE |
| geom | GEOMETRY(MultiPolygon, 4326) | GIST-indexed |
| source | VARCHAR(200) | |
| created_at / updated_at | TIMESTAMPTZ | updated_at via trigger |

### shelters
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(255) | |
| geographic_id | UUID FK → geographic_data | ON DELETE SET NULL |
| geom | GEOMETRY(Point, 4326) | GIST-indexed |
| capacity | INTEGER | |
| facilities | TEXT[] | |
| contact_phone | VARCHAR(30) | |

### citizen_reports *(migration 0004 — mobile app)*
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| reporter_id | UUID FK → users | reporter (any role) |
| geographic_id | UUID FK → geographic_data | ON DELETE SET NULL |
| geom | GEOMETRY(Point, 4326) | GPS location, GIST-indexed |
| severity | INTEGER | 1–5, CHECK |
| description | TEXT | optional |
| status | VARCHAR(20) | `pending` / `verified` / `rejected` (default `pending`) |
| reported_at | TIMESTAMPTZ | default now() |

### emergency_contacts
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name / organization / phone | VARCHAR | NDMA, PDMA Sindh/Punjab, Rescue 1122, … |
| district_name | VARCHAR(150) | plain reference (no FK — contacts may be regional) |

## Integrity features

- `set_updated_at()` trigger keeps `updated_at` current on mutable tables.
- CHECK constraints on probability (0–1), severity (1–5), vulnerability (0–1),
  risk_level values.
- GIST spatial indexes on both `geom` columns; B-tree indexes on all FKs,
  `event_date`, and `email`.
- `v_latest_predictions` view: newest prediction per `geographic_id` (powers
  the GIS risk layer and dashboard distribution).

## Entity relationships

```
users 1───* predictions *───1 geographic_data 1───* flood_events
                                    │ 1───* alerts
                                    │ 1───* shelters
                                    │ 1───* weather_observations
                                    │ 1───1 district_boundaries
```

## Migrations

Schema changes are tracked with Alembic (`backend/alembic/`):

| Revision | Description |
|---|---|
| `0001` | Baseline reproducing `database/schema.sql` (7 tables, `user_role` enum, triggers, indexes, `v_latest_predictions` view) |
| `0002` | `weather_observations` + `district_boundaries` |
| `0003` | `infrastructure`, `vulnerability_indicators`, `resource_allocations` (GIS intelligence) |
| `0004` | `volunteer` role + `citizen_reports` (mobile app event reporting) |

Workflow: `alembic upgrade head` (apply), `alembic upgrade head --sql`
(preview SQL offline), `alembic revision -m "..."` (new migration). See
`database/README.md` for details.
