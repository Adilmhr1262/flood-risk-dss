# Flood Risk Prediction and Early Warning Decision Support System

![Status](https://img.shields.io/badge/status-research--complete-green)
![Tests](https://img.shields.io/badge/tests-119%2F119%20passing-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![PostGIS](https://img.shields.io/badge/PostGIS-3.4-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> Badges above are static project indicators (test count verified 2026-09-26).

A Master's-level disaster management research and software project: a
data-driven platform that helps disaster management authorities, NGOs, and
communities assess flood risk using environmental data, geographic
information, historical flood records, and vulnerability indicators.

> **Terminology note:** this project never uses the two-letter abbreviation for
> artificial intelligence in branding, UI, code, or documentation. Approved
> terms: *data-driven prediction*, *machine learning-based prediction*,
> *risk assessment*, *decision support system*.

## Project status — Phase 4 complete

**Live system:** PostgreSQL 16 + PostGIS 3.4 backend connected and verified.
Start it with `cd backend && .venv/bin/uvicorn app.main:app` (or
`docker compose up`), then open the prototype — it logs in against the live
API and falls back to demo data when the API is unreachable.

| Phase 1 deliverable | Location |
|---|---|
| Complete project structure | `docs/project-structure.md` |
| Database schema (PostgreSQL + PostGIS) + seed data | `database/` |
| Backend architecture (FastAPI + v1 risk engine + ML pipeline) | `backend/` |
| Frontend UI prototype (web dashboard + mobile screens) | `frontend/prototype/` |
| Documentation | `docs/`, `README.md` files |

| Phase 2 deliverable | Location |
|---|---|
| Live PostgreSQL + PostGIS connection | `backend/.env`, `backend/app/db/` |
| Alembic migration files | `backend/alembic/versions/` |
| CSV/GeoJSON import system (validation, dedup, error reports) | `backend/app/services/importers/`, `backend/scripts/import_csv.py`, `POST /api/v1/admin/import/{dataset}` |
| Prediction service + model registry | `backend/app/services/prediction_service.py`, `ml-models/registry.json` |
| Trained model (Random Forest, metrics + feature importance) | `ml-models/models/rf-v1/` |
| Refresh-token auth + role permission matrix | `backend/app/api/v1/auth.py`, `backend/README.md` |
| GIS layers (risk, historical, shelters, contacts, districts, boundaries) | `backend/app/api/v1/gis.py` |
| Dashboard wired to live APIs | `frontend/prototype/assets/api.js` |
| Docker + deployment docs | `docker-compose.yml`, `backend/Dockerfile`, `docs/deployment.md` |
| Extended test suite — 60/60 passing | `backend/tests/` |

| Phase 4 deliverable | Location |
|---|---|
| Migration 0003: `infrastructure`, `vulnerability_indicators`, `resource_allocations` | `backend/alembic/versions/0003_gis_decision_support.py` |
| New GIS layers (risk-layer, historical-floods, vulnerability-map, infrastructure) | `backend/app/api/v1/gis.py` |
| Decision support API (summary, trends, resources) | `backend/app/api/v1/decision_support.py` |
| Authority decision-support dashboard + enriched map popups + SVG time charts | `frontend/prototype/` |
| GIS module documentation | `docs/gis-module.md` |

## Screenshots

Real captures of the working prototype (demo-fallback mode — the UI falls
back to built-in sample data when the API is unreachable):

| Screenshot | View |
|---|---|
| `screenshots/dashboard-map.png` | Dashboard / risk map (authority role) |
| `screenshots/decision-support.png` | Decision Support view |
| `screenshots/alert-center.png` | Authority Alert Center |
| `screenshots/mobile-home.png` | Mobile prototype — home screen (390×844) |
| `screenshots/mobile-risk.png` | Mobile prototype — risk check result (Dadu, HIGH) |

## Quickstart

**View the UI prototype** (no build step — open in a browser; internet
needed for the Leaflet/Chart.js CDNs):

- Web dashboard: `frontend/prototype/index.html`
- Mobile screens: `frontend/prototype/mobile.html`

**Database:**

```bash
createdb flood_risk_dss
psql -d flood_risk_dss -f database/schema.sql
psql -d flood_risk_dss -f database/seed.sql
```

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL and SECRET_KEY
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

**Train a model:**

```bash
cd backend
python -m ml.train --data ml/sample_training_data.csv --out ../ml-models/models/rf-v1
pytest tests/ -v
```

## Repository layout

```
Flood-Risk-DSS/
├── backend/            # FastAPI service layer (app/, alembic/, ml/ training code, scripts/, tests/)
├── frontend/           # Web dashboard prototype (Leaflet map, decision-support, Alert Center)
├── web/                # FloodSafe Pakistan — Next.js public web app (public/authority/volunteer portals)
├── mobile/             # Flutter community app
├── ml-models/          # Model registry (registry.json) + trained artifacts (models/<name>-v1/)
├── database/           # schema.sql, seed.sql
├── datasets/           # raw/ (flood events, weather cache), processed/ (training CSV + DATA_CARD.md), templates/
├── docs/               # research-paper.md, thesis-structure.md, methodology.md, architecture.md, ...
├── figures/            # Publication figures (system architecture, data workflow, model comparison, ...)
├── README.md
└── LICENSE
```

`docs/` additionally holds: `api-spec.md`, `database-schema.md`,
`project-structure.md`, `deployment.md`, `gis-module.md`, `ml-pipeline.md`,
`ml-results.md`, `mobile-app.md`, `early-warning-system.md`,
`contribution.md`, and `img/` (prototype figures from model training).

## System overview

```
Data sources (weather, flood history, GIS, vulnerability)
        │  database/schema.sql (PostGIS)
        ▼
FastAPI backend (/api/v1) ──► v1 weighted risk engine ──► ML pipeline (RF / XGBoost / MLP)
        │
        ├── Web dashboard (authority: monitoring, maps, reports)
        ├── NGO view (affected areas, vulnerability, relief planning)
        └── Mobile app (public: risk check, alerts, emergency info)
```

**Risk classification:** LOW (< 0.33, green) · MEDIUM (0.33–0.66, yellow) ·
HIGH (≥ 0.66, red).

## Roles

| Role | Access |
|---|---|
| `authority` — Disaster Management Authority | Full dashboard, maps, reports, user & alert management |
| `ngo` — NGO / Relief Organization | Affected areas, vulnerability data, relief planning |
| `public` — Public User | Location risk check, alerts, emergency info, safety guidelines |
| `volunteer` — Community Volunteer | Public access + flood-sighting reports (`/mobile/report-event`) |

## Roadmap

- **Phase 1** — Architecture, database design, UI prototype ✅ (this release)
- **Phase 2** — Backend API implementation against live PostgreSQL/PostGIS ✅ (done)
- **Phase 3** — Prediction model training on real historical data, model registry
- **Phase 4** — GIS mapping integration (frontend ↔ `/api/v1/gis`) ✅ (done: advanced GIS layers, decision-support API + dashboard, migration 0003)
- **Phase 5** — Flutter mobile application (`mobile/`) ✅ (done: community app with clean architecture, 8 screens, `/api/v1/mobile` backend + migration 0004, volunteer role, offline support; see `docs/mobile-app.md`)
- **Phase 6** — Testing, documentation, deployment

## Documentation

| Document | Content |
|---|---|
| `docs/research-paper.md` | Research paper draft (final version: IEEE references, Tables I–II, figure captions, data availability) |
| `docs/project-report.md` | Complete project report draft (50–80 page structure) |
| `docs/thesis-structure.md` | Master's thesis chapter outline |
| `docs/research-proposal.md` | Concise Master's research proposal with 12-month timeline |
| `docs/contribution.md` | Research contribution statement |
| `docs/methodology.md` | Research methodology |
| `docs/architecture.md` | System architecture |
| `docs/ml-pipeline.md`, `docs/ml-results.md` | Model development and results |
| `docs/early-warning-system.md` | Early warning automation |
| `docs/gis-module.md` | GIS module guide |
| `docs/mobile-app.md` | Flutter community app (architecture, screens, API map) |
| `docs/api-spec.md` | REST API specification |
| `docs/api-examples.md` | curl usage examples for all main flows |
| `docs/installation.md` | Installation guide |
| `docs/environment-setup.md` | Environment variables reference |
| `docs/deployment.md` | Deployment guide |
| `docs/deployment-checklist.md` | Pre-production deployment checklist |
| `docs/quality-review.md` | Final quality review report |
| `docs/database-schema.md` | Database design |
| `docs/project-structure.md` | Folder layout and conventions |
| `docs/presentation/` | 12-slide supervisor presentation (PPTX) |
| `backend/README.md`, `database/README.md` | Component guides |

## Citation

If you use this software or the accompanying research, please cite it as
described in [`CITATION.cff`](CITATION.cff):

> Mahar, A. A. (2026). *Flood Risk Prediction and Early Warning Decision
> Support System* (v1.0.0) [Computer software].

## Research context

Built as the software artefact for Master's research in Disaster Management:
*A Machine Learning-Based Flood Risk Prediction Framework Using Environmental
and Geospatial Data for Disaster Risk Reduction.* Seed data focuses on
Pakistan (Sindh/Punjab), including the 2010 super floods and the 2022
monsoon floods.
