# Project Structure

```
flood-risk-dss/
├── README.md                    # Project overview, quickstart, roadmap
├── docs/
│   ├── methodology.md           # Research methodology (Master's level)
│   ├── api-spec.md              # REST API specification
│   ├── database-schema.md       # Database design documentation
│   └── project-structure.md     # This file
├── database/
│   ├── schema.sql               # PostgreSQL 15 + PostGIS DDL
│   ├── seed.sql                 # Seed data (Sindh/Punjab districts, flood history)
│   └── README.md                # Database setup guide
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── README.md
│   ├── app/
│   │   ├── main.py              # App factory, CORS, router registration
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── core/
│   │   │   ├── security.py      # Password hashing, JWT
│   │   │   └── deps.py          # get_db, get_current_user, require_role
│   │   ├── db/
│   │   │   ├── session.py       # Engine + SessionLocal
│   │   │   └── base.py          # Declarative base
│   │   ├── models/              # SQLAlchemy models (mirror database/schema.sql)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── risk_engine.py   # Deterministic v1 weighted risk scorer
│   │   └── api/v1/
│   │       ├── auth.py          # Register, login, /me
│   │       ├── users.py         # User management (authority only)
│   │       ├── dashboard.py     # Summary cards, trends, distributions
│   │       ├── risk.py          # POST /predict, prediction history
│   │       ├── gis.py           # GeoJSON risk + historical layers
│   │       ├── alerts.py        # Alert CRUD
│   │       └── reports.py       # CSV risk reports
│   ├── ml/
│   │   ├── pipeline.py          # sklearn: clean → features → train → evaluate
│   │   ├── train.py             # CLI: python -m ml.train --data ... --out ...
│   │   └── sample_training_data.csv
│   └── tests/
│       └── test_risk_engine.py
├── frontend/
│   └── prototype/               # Phase 1 clickable UI prototype (no build step)
│       ├── index.html           # Web dashboard prototype
│       ├── mobile.html          # Mobile app screen mockups
│       └── assets/
│           ├── style.css
│           └── app.js
└── mobile/                      # Phase 5: Flutter application (planned)
```

## Module → directory mapping

| Spec module | Location |
|---|---|
| User authentication | `backend/app/api/v1/auth.py`, `core/security.py`, `models/` (users) |
| Dashboard | `backend/app/api/v1/dashboard.py`, `frontend/prototype/index.html` (dashboard page) |
| Flood risk assessment | `backend/app/services/risk_engine.py`, `backend/app/api/v1/risk.py`, `backend/ml/` |
| GIS flood risk map | `backend/app/api/v1/gis.py`, PostGIS in `database/schema.sql`, Leaflet map in prototype |
| Mobile application | `frontend/prototype/mobile.html` (Phase 1 mockups) → `mobile/` Flutter (Phase 5) |
| Prediction engine | `backend/ml/pipeline.py`, `backend/ml/train.py` |
| Database | `database/schema.sql`, `database/seed.sql` |

## Conventions

- **Terminology:** the two-letter abbreviation for artificial intelligence is
  never used in code, UI, or docs. Approved
  terms: *data-driven prediction*, *machine learning-based prediction*,
  *risk assessment*, *decision support system*.
- **API prefix:** all endpoints under `/api/v1`; health check at `/health`.
- **Database:** PostgreSQL 15 + PostGIS; UUID primary keys; geometries in
  SRID 4326; timestamps in UTC (`TIMESTAMPTZ`).
- **Auth:** JWT bearer tokens; roles `authority`, `ngo`, `public`.
- **Theme:** dark blue / white / emergency orange-red.
