# Deployment Guide

## 1. Local development run

Prerequisites: Python 3.12, PostgreSQL 15+ with PostGIS.

```bash
# 1. Database
createdb flood_risk_dss
psql -d flood_risk_dss -f database/schema.sql
psql -d flood_risk_dss -f database/seed.sql
# (when available) alembic upgrade head   # applies pending migrations

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit: DATABASE_URL, SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- Interactive docs: `http://localhost:8000/docs`
- UI prototype: open `frontend/prototype/index.html` in a browser and log in
  with a demo account (e.g. `authority.demo@flooddss.pk` / `demo1234`);
  the prototype calls the live API and falls back to sample data if the
  backend is unreachable. Override the API base with
  `localStorage.FR_DSS_API_BASE = "http://host:8000/api/v1"`.

Run the test suite:

```bash
cd backend
TEST_DATABASE_URL=postgresql+psycopg2://flood_dss:flood_dss_dev@localhost:5432/flood_risk_dss_test \
  .venv/bin/python -m pytest tests/ -v
```

## 2. Docker Compose run

```bash
cp backend/.env.example backend/.env   # set SECRET_KEY + POSTGRES_PASSWORD
docker compose up --build -d
# Load schema + seed into the containerised database (first run only):
docker compose exec -T db psql -U flood_dss -d flood_risk_dss < database/schema.sql
docker compose exec -T db psql -U flood_dss -d flood_risk_dss < database/seed.sql
# (when available) docker compose exec api alembic upgrade head
docker compose logs -f api
```

Services: `db` → `postgis/postgis:16-3.4` with a named volume (`pgdata`) and
a `pg_isready` healthcheck; `api` → builds `backend/Dockerfile`, waits for a
healthy database, serves on `${API_PORT:-8000}`. The compose file overrides
`DATABASE_URL` to point at the `db` service; keep other values in
`backend/.env`.

## 3. Production checklist

- **Secrets**: generate a long random `SECRET_KEY`
  (`python -c "import secrets; print(secrets.token_hex(32))"`); never commit
  `.env`. Rotate `POSTGRES_PASSWORD`.
- **Database**: run `alembic upgrade head` on every deploy; back up with
  `pg_dump -Fc` on a schedule and test restores; keep the PostGIS version
  pinned (`postgis/postgis:16-3.4`).
- **CORS**: replace the permissive default with the exact frontend origins,
  e.g. `CORS_ORIGINS=https://dss.example.org`; never use `*` with credentials.
- **Workers**: the Dockerfile runs uvicorn with `--workers 2`; scale workers
  to CPU cores behind a reverse proxy (nginx/Caddy) terminating TLS.
- **Tokens**: keep `ACCESS_TOKEN_EXPIRE_MINUTES` short (15–60);
  `REFRESH_TOKEN_EXPIRE_DAYS=7` is a sane default. Logout is stateless —
  clients discard tokens.
- **Observability**: ship uvicorn access logs, add request logging, and
  monitor `/health`. Alert on 5xx rate and on database connection failures
  (endpoints return `503` when the database is unreachable).
- **Data**: re-run model training (`python -m ml.train`) when new historical
  data is imported via `/api/v1/admin/import/{dataset}`; record the new
  `model_version` in `docs/` and the model registry.
