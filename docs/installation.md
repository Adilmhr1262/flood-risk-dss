# Installation Guide

Step-by-step setup of the Flood Risk Prediction and Early Warning Decision
Support System for local development and evaluation.

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12 | Backend, training scripts, docs tooling |
| PostgreSQL | 16 | With the PostGIS 3.4 extension |
| Git | any | To clone the repository |
| Flutter | 3.47.5 | Only for the mobile app (`mobile/`) |
| Node/npm | — | Not required (no JS build step; prototype is static) |

Check versions:

```bash
python3 --version        # 3.12.x
psql --version           # 16.x
psql -c "SELECT PostGIS_Version();"   # 3.4.x (needs a running server)
```

Install PostGIS on Ubuntu/Debian:

```bash
sudo apt install postgresql-16 postgresql-16-postgis-3
```

## 2. Clone

```bash
git clone https://github.com/aadilmahar/flood-risk-dss   # placeholder URL
cd flood-risk-dss
```

## 3. Database

```bash
createdb flood_risk_dss
psql -d flood_risk_dss -f database/schema.sql
psql -d flood_risk_dss -f database/seed.sql
```

`schema.sql` creates the PostGIS-enabled schema (7 core tables);
`seed.sql` loads 52 historical flood events, 12 districts, demo users,
shelters, and emergency contacts. Demo logins (password `demo1234`):

- `authority.demo@flooddss.pk` — authority role
- `ngo.demo@flooddss.pk` — NGO role
- `public.demo@flooddss.pk` — public role

## 4. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` — at minimum set:

```bash
DATABASE_URL=postgresql+psycopg2://flood_dss:YOUR_PASSWORD@localhost:5432/flood_risk_dss
SECRET_KEY=<long random string>   # python -c "import secrets; print(secrets.token_hex(32))"
```

The schema can also be managed with Alembic (migrations for Phases 2–6
live in `backend/alembic/versions/`):

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- Interactive API docs: `http://localhost:8000/docs`

## 5. Web dashboard prototype

No build step. Open `frontend/prototype/index.html` in a browser (internet
needed once for the Leaflet/Chart.js CDNs). It calls the live API at
`http://localhost:8000/api/v1` and falls back to bundled demo data when the
backend is unreachable. To point at another host:

```js
localStorage.FR_DSS_API_BASE = "http://192.168.1.10:8000/api/v1";
```

## 6. Model training (optional)

Trained artifacts ship in `ml-models/`, so training is not required to run
the system. To reproduce the Phase 3 results:

```bash
cd backend
.venv/bin/python ml/fetch_weather.py     # fills datasets/raw/weather/ (slow)
.venv/bin/python ml/build_dataset.py     # writes datasets/processed/sindh_training_2010_2024.csv
.venv/bin/python ml/train_phase3.py      # trains RF / XGBoost / MLP -> ml-models/
sha256sum ../datasets/processed/sindh_training_2010_2024.csv
# expected: 4b478ea58d6af1f91dd65540bc32cb3e770badc428313c779d76b2700418fb62
```

## 7. Mobile app (optional)

Requires Flutter 3.47.5 and (for APKs) the Android SDK:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter run                        # device / emulator
flutter build apk --release        # Android APK (needs Android SDK)
flutter build web --release        # web build (no SDK needed)
```

Point the app at your API by editing the base URL in
`mobile/lib/core/config/` (see `docs/mobile-app.md`).

## 8. Verify the install

```bash
cd backend
.venv/bin/python -m pytest tests/ -q -p no:cacheprovider
# expected: 119 passed
curl -s http://localhost:8000/health
```

## 9. Docker alternative

```bash
cp backend/.env.example backend/.env   # set SECRET_KEY + POSTGRES_PASSWORD
docker compose up --build -d
docker compose exec -T db psql -U flood_dss -d flood_risk_dss < database/schema.sql
docker compose exec -T db psql -U flood_dss -d flood_risk_dss < database/seed.sql
```

See `docs/deployment.md` for production deployment and
`docs/deployment-checklist.md` for the pre-production checklist.
