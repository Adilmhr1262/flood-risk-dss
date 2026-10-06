# API Specification

Base URL: `/api/v1` · Auth: JWT bearer token (`Authorization: Bearer <token>`)
· Health: `GET /health`

Roles: `authority` (Disaster Management Authority), `ngo` (NGO / Relief
Organization), `public` (Public User).

## Auth — `/api/v1/auth`

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/register` | open | Register user (name, email, password, role, location). Returns access + refresh JWT pair. |
| POST | `/auth/login` | open | Login with email + password. Returns access + refresh JWT pair. |
| POST | `/auth/refresh` | open | Exchange a valid refresh token for a new pair. `401` on invalid/expired token. |
| POST | `/auth/logout` | authenticated | Stateless logout — client discards both tokens. Documented no-op. |
| GET | `/auth/me` | authenticated | Current user profile. |

Passwords are hashed with bcrypt (passlib). Access tokens are short-lived
(`ACCESS_TOKEN_EXPIRE_MINUTES`); refresh tokens live `REFRESH_TOKEN_EXPIRE_DAYS`
and carry a `type: "refresh"` claim — refresh tokens are rejected as API
credentials. Demo accounts (seeded): `authority.demo@flooddss.pk`,
`ngo.demo@flooddss.pk`, `public.demo@flooddss.pk` (password `demo1234` in dev).

## Users — `/api/v1/users` (authority only)

| Method | Path | Description |
|---|---|---|
| GET | `/users` | Paginated user list |
| GET | `/users/{id}` | User detail (UUID) |
| PATCH | `/users/{id}` | Update user |
| DELETE | `/users/{id}` | Delete user |

## Dashboard — `/api/v1/dashboard`

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/dashboard/summary` | authority, ngo | Summary cards: active flood alerts, high risk areas, total historical events, current risk status |
| GET | `/dashboard/rainfall-trends` | authority, ngo | Monthly rainfall trend points |
| GET | `/dashboard/flood-frequency` | authority, ngo | Flood events per year |
| GET | `/dashboard/risk-distribution` | authority, ngo | Count of districts per risk level (LOW/MEDIUM/HIGH) |

## Risk — `/api/v1/risk`

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/risk/predict?model={rf-v1\|rule-based-v1}` | authenticated | Assess flood risk for a district; every assessment is stored in `predictions` |
| GET | `/risk/predictions` | authenticated | Paginated prediction history (filter by district) |
| GET | `/risk/model-info` | authenticated | Model registry: available models, metrics, feature importance |

### POST /risk/predict — request

```json
{
  "district_name": "Dadu",
  "rainfall_mm": 180.5,
  "temperature_c": 34.0,
  "humidity_pct": 82.0,
  "elevation_m": 42.0,
  "river_distance_km": 3.2,
  "slope_deg": 1.5,
  "population_density": 210.0,
  "prev_flood_events": 4,
  "last_severity": 5
}
```

`last_severity` scale: 0=None, 1=Minor, 2=Moderate, 3=Severe, 4=Very severe,
5=Catastrophic — the same scale as `flood_events.severity` in the database.

### POST /risk/predict — response

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "geographic_id": "…",
  "district_name": "Dadu",
  "probability": 0.82,
  "risk_level": "HIGH",
  "main_factors": ["Heavy rainfall", "Low elevation", "River proximity"],
  "recommendations": [
    "Prepare evacuation plans",
    "Monitor water levels",
    "Contact emergency services"
  ],
  "model_version": "v1.0.0-rule-based",
  "predicted_at": "2026-09-26T07:00:00Z"
}
```

## GIS — `/api/v1/gis`

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/gis/risk-layers` | authenticated | GeoJSON `FeatureCollection` of districts with latest risk level + probability |
| GET | `/gis/historical-layers` | authenticated | GeoJSON of historical flood event locations |
| GET | `/gis/shelters` | authenticated | GeoJSON of emergency shelter / relief camp points (name, capacity, facilities, contact phone) |
| GET | `/gis/emergency-contacts?district_name=` | authenticated | JSON list of rescue/relief contacts, optionally filtered by district |
| GET | `/gis/districts` | authenticated | GeoJSON of all registered districts with full attributes (elevation, river distance, slope, population density, vulnerability index) |
| GET | `/gis/boundaries` | authenticated | GeoJSON of district boundary polygons — `404` until the boundaries migration is applied |

Risk layer properties per feature: `district_name`, `risk_level`
(`LOW`/`MEDIUM`/`HIGH`), `probability`, `color`, `main_factors`,
`model_version`, `predicted_at`.

### Phase 4 GIS intelligence layers

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/gis/risk-layer` | authenticated | GeoJSON — one feature per district with current risk (`NO_DATA` when no prediction exists) |
| GET | `/gis/historical-floods?district_name=&from_year=&to_year=` | authenticated | GeoJSON of flood events with `year`, `severity`, `severity_label`, `affected_population`, `source` |
| GET | `/gis/vulnerability-map` | authenticated | GeoJSON — per-district `vulnerability_index`, `population_density`, `risk_level`, computed `priority` (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`) |
| GET | `/gis/infrastructure?type=&district_name=` | authenticated | GeoJSON of hospitals, rescue centres, emergency facilities (`is_sample_data` flags illustrative rows) |

## Decision support — `/api/v1/decision-support`

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/decision-support/summary` | authority, ngo | Operational summary: `high_risk_districts` (probability, top contributing factors, recommended actions), `active_alerts`, `latest_predictions`, `resource_overview` (shelters, infrastructure counts, allocation status), `vulnerability_hotspots`; authority role additionally receives `allocations` |
| GET | `/decision-support/trends` | authority, ngo | `year_wise` flood counts per district with a simple 2017–2024 vs 2010–2016 trend indicator, `seasonal_pattern` (events per month) |
| GET | `/decision-support/resources` | authority, ngo | Resource allocations with district names |
| POST | `/decision-support/resources` | authority | Record an allocation: `{district_name, resource_type, quantity, status, notes}` |

## Admin — `/api/v1/admin` (authority only)

| Method | Path | Description |
|---|---|---|
| POST | `/admin/import/{dataset}` | Multipart file import with validation, duplicate checking, per-row error reporting and `?dry_run=true` mode. Datasets: `flood_events`, `weather`, `geographic` (CSV), `boundaries` (GeoJSON). Returns an import report JSON. |
| GET | `/admin/import/templates/{dataset}` | Download the sample import file (headers + example rows) for a dataset |

## Alerts — `/api/v1/alerts`

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/alerts` | authenticated | Paginated alerts (active first) |
| POST | `/alerts` | authority, ngo | Create alert (title, message, severity, geographic_id) |
| PATCH | `/alerts/{id}/deactivate` | authority, ngo | Deactivate alert |
| DELETE | `/alerts/{id}` | authority | Delete alert |

## Mobile — `/api/v1/mobile` (Flutter community app)

Roles: `public`, `volunteer` (public read + event reporting), `ngo`, `authority`.

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/mobile/my-risk?district_name=` or `?lat=&lon=` | public, volunteer, ngo, authority | Latest risk assessment for a district or GPS point |
| GET | `/mobile/alerts?district_name=` | public, volunteer, ngo, authority | Active warnings, newest first |
| GET | `/mobile/shelters/nearby?lat=&lon=&radius_km=` | public, volunteer, ngo, authority | Shelters ordered by geodesic distance |
| GET | `/mobile/emergency-contacts?district_name=` | public, volunteer, ngo, authority | Rescue directory |
| POST | `/mobile/report-event` | public, volunteer, ngo, authority | Flood sighting report → `citizen_reports` (`pending` triage) |
| GET | `/mobile/reports/mine` | public, volunteer, ngo, authority | Own reports |

## Reports — `/api/v1/reports`

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/reports/risk-report` | authority, ngo | CSV export of predictions (filters: district, risk_level, date range) |
| GET | `/reports/historical-events` | authority, ngo | CSV export of flood events |

## Error format

```json
{ "detail": "District 'Dadu' not found" }
```

Standard HTTP codes: `400` validation, `401` unauthenticated, `403`
forbidden (role), `404` not found, `503` database unavailable (endpoints
gracefully degrade when `DATABASE_URL` is unreachable; `POST /risk/predict`
still returns an assessment with `id: null`).
