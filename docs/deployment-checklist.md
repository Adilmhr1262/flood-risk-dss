# Production Deployment Checklist

Bringing the Flood Risk Prediction and Early Warning Decision Support System
from the development VM to a production server. Stack: FastAPI backend,
PostgreSQL 16 + PostGIS 3.4, static HTML/JS prototype frontend (Leaflet),
Flutter mobile app. Terminology: "machine learning-based" / "data-driven" /
"decision support" — never branded with artificial-intelligence terminology.

---

## A. Backend

### A1. Server requirements

- [ ] OS: Ubuntu 22.04 LTS or newer
- [ ] CPU/RAM: minimum suggested 2 vCPU / 4 GB RAM (single-instance; the
      APScheduler early-warning loop must run on exactly one API instance)
- [ ] Python 3.12
- [ ] PostgreSQL 16 + PostGIS 3.4 (pinned: `postgis/postgis:16-3.4` image)
- [ ] Outbound HTTPS to Open-Meteo (forecast ingestion) and Firebase
      (FCM push) allowed from the server

### A2. Environment variables (from `backend/app/config.py`)

Copy `backend/.env.example` to `.env` and set every value:

| Variable | Purpose / notes |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg2://flood_dss:<password>@db:5432/flood_risk_dss` |
| `TEST_DATABASE_URL` | Test database URL (not used in production, keep unset/placeholder) |
| `SECRET_KEY` | **JWT signing secret** — generate fresh (see hardening) |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Short in production, 15–60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 (sane default) |
| `CORS_ORIGINS` | Exact frontend origin(s), comma-separated — never `*` with credentials |
| `APP_ENV` | `production` |
| `MODEL_VERSION` | Informational version label |
| `EW_SCHEDULER_ENABLED` | `true` on the one scheduler instance, `false` everywhere else |
| `EW_CYCLE_MINUTES` | Warning-cycle interval (default 30) |
| `EW_ALERT_COOLDOWN_HOURS` | Same-level alert deduplication (default 6) |
| `EW_DEFAULT_MODEL` | Registry model for the cycle (`mlp-v1` default, best observed F1; `rule-based-v1` available as transparent fallback) |
| `EW_FORECAST_DAYS` | Open-Meteo forecast horizon (default 2) |
| `FCM_SERVICE_ACCOUNT_PATH` | Path to Firebase service-account JSON (without it, push runs log-only degraded mode) |

### A3. Database setup

- [ ] `createdb flood_risk_dss`
- [ ] `psql -d flood_risk_dss -f database/schema.sql`
- [ ] `psql -d flood_risk_dss -f database/seed.sql`
- [ ] `alembic upgrade head` (apply on **every** deploy)
- [ ] Import production data: district polygons, authoritative infrastructure
      registries (replacing `is_sample_data` rows), shelter list
- [ ] Create the first `authority` user (authorities cannot self-register)
- [ ] Verify demo accounts are disabled or removed:
      `authority.demo@flooddss.pk`, `ngo.demo@flooddss.pk`,
      `public.demo@flooddss.pk` (password `demo1234`) are dev-only

### A4. Deploy and serve (Docker Compose or systemd)

- [ ] `cp backend/.env.example backend/.env` → set `SECRET_KEY`,
      `POSTGRES_PASSWORD`, all EW_* values
- [ ] `docker compose up --build -d` (db healthcheck-gated; api waits for
      healthy db; serves `${API_PORT:-8000}`)
- [ ] `GET /health` returns 200; `GET /docs` reachable internally
- [ ] `GET /api/v1/early-warning/status` confirms the scheduler is running
      on the one scheduler instance

systemd sketch (alternative to Compose, `backend` already has a Dockerfile):

```ini
# /etc/systemd/system/flood-dss-api.service
[Unit]
Description=Flood Risk DSS API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=flooddss
WorkingDirectory=/opt/flood-risk-dss/backend
EnvironmentFile=/opt/flood-risk-dss/backend/.env
ExecStart=/opt/flood-risk-dss/backend/.venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- [ ] `systemctl daemon-reload && systemctl enable --now flood-dss-api`
- [ ] One and only one instance has `EW_SCHEDULER_ENABLED=true`
      (APScheduler is in-process — duplicates double-issue alerts)

### A5. Reverse proxy + TLS

- [ ] nginx or Caddy in front of uvicorn, terminating TLS (Let's Encrypt)
- [ ] Proxy only `/api/v1` (+ `/docs` if wanted internally) to
      `127.0.0.1:8000`; serve the frontend statically
- [ ] Set `CORS_ORIGINS` to the exact frontend origin(s)

### A6. Production hardening (explicit)

- [ ] **SECRET_KEY rotation:** generate a long random secret
      (`python -c "import secrets; print(secrets.token_hex(32))"`); never
      commit `.env`; rotate on staff changes
- [ ] **CORS restriction:** exact origins only, never `*`
- [ ] **HTTPS everywhere:** TLS on the proxy; the API never exposed
      directly on a public port
- [ ] **Backups:** scheduled `pg_dump -Fc` of `flood_risk_dss` with
      off-site copies; **test restores** before relying on them
- [ ] **Short access-token expiry:** `ACCESS_TOKEN_EXPIRE_MINUTES` 15–60
- [ ] **Remove dev credentials:** rotate `POSTGRES_PASSWORD`; delete or
      disable demo accounts
- [ ] **FCM credentials:** service-account JSON with minimal Cloud
      Messaging rights, readable only by the app user
- [ ] **Observability:** ship uvicorn access logs; monitor `/health`;
      alert on 5xx rate and on database connection failures (endpoints
      return 503 when the DB is unreachable)
- [ ] **Retrain cadence:** re-run `python -m ml.train` when new historical
      data is imported via `/api/v1/admin/import/{dataset}`; record the
      new model version in the registry and `docs/`

---

## B. Frontend (static prototype)

- [ ] The prototype is static HTML/JS — host on any static host
      (nginx `root`, Caddy `file_server`, S3/CloudFront, GitHub Pages…)
- [ ] Point it at the production API before or after deploy:
      `localStorage.FR_DSS_API_BASE = "https://<api-host>/api/v1"`
      (the prototype falls back to bundled sample data when the API is
      unreachable — verify the fallback does not mask a misconfigured base)
- [ ] Serve over HTTPS from the same origin policy that `CORS_ORIGINS`
      allows
- [ ] Verify login with a real account, live risk map, decision-support
      page, and the Authority Alert Center triage queue

---

## C. Mobile (Flutter 3.47.5)

### C1. Android build

- [ ] Install Android Studio + Android SDK on the build machine
      (the SDK is not required in dev; the release web build passing
      proves the Dart compiles)
- [ ] `cd mobile && flutter pub get`
- [ ] `flutter build apk --release --dart-define=API_BASE_URL=https://<api-host>/api/v1`
- [ ] Sign the APK/AAB with a release keystore; keep the keystore and its
      passwords out of the repo (build via CI — Codemagic/GitHub Actions —
      is the recommended path)

### C2. FCM pending integration step

- [ ] Add `firebase_messaging` to `pubspec.yaml`
- [ ] Add `google-services.json` (Android) / `GoogleService-Info.plist`
      (iOS) — never committed to the repo
- [ ] Request notification permission; call
      `NotificationService.registerToken(await FirebaseMessaging.instance.getToken())`
      after login, `unregisterToken()` on logout
      (see `lib/features/alerts/data/notification_service.dart`)
- [ ] Server side: set `FCM_SERVICE_ACCOUNT_PATH`; note push currently
      multicasts to **all** registered devices — per-district subscriptions
      are the next step before geo-targeted warnings
- [ ] Until push is live, the app inbox (`/mobile/alerts`) is the reliable
      alert channel; verify it works offline via the shared-preferences
      cache

---

## D. Go-live smoke tests

- [ ] Register → login → refresh-on-401 → logout (JWT lifecycle)
- [ ] `/risk/predict?model=mlp-v1` returns probability + contributing
      factors + recommendations
- [ ] Trigger one manual early-warning cycle; confirm alert row, 6h
      cooldown dedup, and MEDIUM→HIGH escalation behave per
      `docs/early-warning-system.md`
- [ ] Volunteer `POST /mobile/report-event` → authority verify/reject in
      the Alert Center
- [ ] GIS layers render: risk, historical floods, vulnerability map,
      shelters, infrastructure
- [ ] `pg_dump -Fc` completes and a test restore succeeds
