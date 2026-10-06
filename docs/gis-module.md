# GIS Module — Flood Risk DSS

Phase 4 documentation: advanced GIS visualization and decision support for
disaster management authorities.

## 1. GIS architecture

```
PostGIS (geographic_data, shelters, infrastructure,
         district_boundaries, vulnerability_indicators)
        │  SQL + GeoAlchemy2
        ▼
FastAPI  /api/v1/gis/*  →  GeoJSON FeatureCollection
FastAPI  /api/v1/decision-support/*  →  operational JSON views
        │  fetch + JWT
        ▼
Leaflet 1.9.4 (frontend/prototype) — layer groups, popups, legend
```

All geometry is stored in SRID 4326 (WGS 84). The API converts PostGIS
geometries to GeoJSON server-side (`ST_AsGeoJSON` for polygons,
GeoAlchemy2 `to_shape` for points); the client renders them as Leaflet
layers without any further transformation. Every GIS endpoint requires
authentication (JWT bearer token); decision-support endpoints additionally
enforce the authority/ngo role matrix.

## 2. Data sources per layer

| Layer | Endpoint | Source table(s) | Notes |
|---|---|---|---|
| Risk | `/gis/risk-layer`, `/gis/risk-layers` | `predictions` ⨝ `geographic_data` | Latest prediction per district; `NO_DATA` when none exists |
| Historical floods | `/gis/historical-floods` | `flood_events` ⨝ `geographic_data` | Documented events; severity 1–5 with labels |
| Vulnerability | `/gis/vulnerability-map` | `vulnerability_indicators` ⨝ `geographic_data` (+ latest prediction) | Composite index from the Phase 3 research dataset (see `datasets/processed/DATA_CARD.md`) |
| Infrastructure | `/gis/infrastructure` | `infrastructure` ⨝ `geographic_data` | Hospitals, rescue centres, emergency facilities |
| Shelters | `/gis/shelters` | `shelters` ⨝ `geographic_data` | Relief camps with capacity and facilities |
| District boundaries | `/gis/boundaries` | `district_boundaries` | Polygons when the boundaries dataset is imported |
| Emergency contacts | `/gis/emergency-contacts` | `emergency_contacts` | Directory (JSON, not GeoJSON) |

Infrastructure seed rows are **clearly-marked sample data**
(`is_sample_data = true`): plausible names and positions offset from
district centroids. They must be replaced with authoritative PDMA / Health
Department registries before operational use. The API surfaces the flag so
the UI can warn users.

## 3. Map methodology

### 3.1 Risk classification

Districts are coloured from their latest stored prediction:

- `HIGH` — probability ≥ 0.66 (red)
- `MEDIUM` — 0.33 ≤ probability < 0.66 (amber)
- `LOW` — probability < 0.33 (green)

Thresholds match the rule-based engine and the trained classifiers'
decision boundaries (`risk_level()` in `app/services/risk_engine.py`).

### 3.2 Vulnerability priority

`vulnerability_index` is the Phase 3 composite (0–1, higher = more
vulnerable). The decision priority combines it with current risk:

- `CRITICAL` — HIGH risk **and** vulnerability_index ≥ 0.33
- `HIGH` — HIGH risk, **or** vulnerability_index ≥ 0.40
- `MEDIUM` — MEDIUM risk, **or** vulnerability_index ≥ 0.25
- `LOW` — otherwise

Implemented in `_priority_class()` (`backend/app/api/v1/gis.py`) and reused
by the decision-support summary so the map and the dashboard always agree.

### 3.3 Time analysis

`/decision-support/trends` aggregates `flood_events` by district and year
(2010–2024). The trend indicator compares mean yearly event counts for
2017–2024 against 2010–2016 (`increasing` / `decreasing` / `stable`,
±25% bands). The seasonal pattern counts events per calendar month across
all years, exposing the monsoon (Jul–Sep) concentration. Counts reflect
*documented* events only — under-reporting of minor floods is a known
limitation (see `datasets/processed/DATA_CARD.md`).

## 4. Decision support workflow

```
1. Data        district attributes · weather · documented flood history
2. Prediction  /risk/predict?model=…  →  probability + risk level (persisted)
3. Explanation recomputed per-feature contributions (model explainability)
               or stored main factors as fallback
4. Action      rule-based recommendations per risk level
               (evacuation planning, monitoring, shelter referral)
5. Resources   shelters + capacity · infrastructure by type ·
               allocations by status · vulnerability hotspots
6. Review      trends + seasonal pattern inform pre-monsoon planning
```

`GET /decision-support/summary` packages steps 2–5 into a single
operational view for the authority dashboard: high-risk districts with
their explanation and recommended actions, active alerts, latest
predictions with model versions, the resource overview, and vulnerability
hotspots. The authority role additionally receives the full resource
allocation list and may record new allocations
(`POST /decision-support/resources`).

## 5. Frontend

`frontend/prototype/index.html` hosts the **Decision Support** view
(authority/ngo roles) and the GIS map page:

- Layer controls toggle Risk, Historical floods, Vulnerability,
  Infrastructure and District boundaries independently.
- District click popups show risk probability/level, contributing factors
  with contribution shares, recommended actions, vulnerability index and
  priority, and shelter capacity in the district.
- The district search box zooms to and opens the matching district.
- The decision panel renders high-risk districts, active alerts, latest
  predictions (with model version), resource overview and hotspots from the
  live API, with built-in demo data when the API is unreachable.
- Time analysis charts are dependency-free inline SVG bar charts (year-wise
  totals and monthly seasonal pattern) so the page works offline.

## 6. Limitations

- Vulnerability indicators are static district-level composites; they do
  not yet capture intra-district variation or real-time exposure.
- Infrastructure locations are sample data until replaced by authoritative
  registries.
- Trend analysis inherits the reporting bias of the underlying event
  records (documented vs. actual floods).
- The map renders district centroids as points; true choropleth rendering
  requires the `district_boundaries` polygon dataset.

## 7. Spatial type convention

All spatial columns in this project — including `infrastructure.location` —
use `Geometry(POINT, 4326)` rather than `geography`. This is a deliberate,
project-wide convention: every table, spatial index, migration and GeoJSON
serializer is built on the geometry type, and mixing in a single geography
column would complicate queries and break that consistency. For a
district-scale decision support system the planar calculations are
adequate; a future operational deployment can migrate to geography if
geodesic accuracy becomes a requirement.
