# FloodSafe Pakistan — Production Deployment Guide

How to deploy the complete platform (FastAPI backend, PostgreSQL/PostGIS
database, Next.js frontend) as a real, publicly accessible disaster
management system. Written for a single Ubuntu 22.04/24.04 LTS server;
adapt paths for other distributions.

Architecture (production):

```
                 ┌─────────────┐
Internet ──TLS─▶ │    nginx    │  (443 → 80 redirect, static security headers)
                 └──────┬──────┘
                        ├─ /api/* ──▶ uvicorn (127.0.0.1:8000, --proxy-headers)
                        └─ /* ──────▶ Next.js (127.0.0.1:3000, next start)
                                          │
                                     PostgreSQL 16 + PostGIS 3.4
```

## 1. Server requirements

- Ubuntu 22.04/24.04 LTS, 4 GB RAM minimum (8 GB recommended), 40 GB disk.
- Public DNS A record pointing at the server, e.g. `floodsafe.example.pk`
  (API served from the same domain under `/api` — no CORS needed at all
  in this layout, see §5).
- Ports 80/443 open; 8000/3000/5432 bound to localhost only.

Install the base packages:

```bash
sudo apt update && sudo apt install -y \
  postgresql-16 postgresql-16-postgis-3 \
  python3.12-venv nginx certbot python3-certbot-nginx \
  nodejs npm
```

## 2. Database setup (PostgreSQL + PostGIS)

```bash
# Dedicated least-privilege role (no CREATEDB, no SUPERUSER).
sudo -u postgres psql <<'EOF'
CREATE ROLE flood_app WITH LOGIN PASSWORD '<strong-random-password>';
CREATE DATABASE flood_prod OWNER flood_app;
\c flood_prod
CREATE EXTENSION IF NOT EXISTS postgis;
EOF
```

Run the migrations (reproduces the full schema from an empty database):

```bash
cd flood-risk-dss/backend
cp .env.example .env        # then edit: DATABASE_URL, SECRET_KEY, CORS_ORIGINS
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DATABASE_URL="postgresql+psycopg2://flood_app:<password>@localhost:5432/flood_prod" \
  .venv/bin/alembic upgrade head
.venv/bin/alembic current   # must print: 0006 (head)
```

Load the reference data (districts, shelters, contacts, flood history):

```bash
# See docs/database-schema.md § seeding; the canonical order is:
#   schema objects via migrations (above), then datasets/* CSV imports
#   via the admin import endpoints or scripts described in docs/deployment.md.
```

Verify: `psql "postgresql://flood_app:<pw>@localhost:5432/flood_prod" -c "\dt"`
should list all application tables, and `SELECT PostGIS_version();`
must return 3.x.

### Backup strategy

- Nightly logical backup: `scripts/backup-db.sh` (pg_dump custom format,
  rotation keeps the last 14 days by default). Install the cron job:

```cron
0 2 * * * /srv/flood-risk-dss/scripts/backup-db.sh >> /var/log/floodsafe-backup.log 2>&1
```

- Backups land in `database/backups/flood_risk_dss-YYYY-MM-DD_HHMM.dump`.
  Copy them off-server (object storage or a second host) — a backup on the
  same disk is not a backup.
- Test restores quarterly on a scratch database:

```bash
pg_restore -d flood_restore_test --clean database/backups/<file>.dump
```

- Restore procedure (disaster recovery):

```bash
# 1. Stop the API so nothing writes mid-restore.
sudo systemctl stop floodsafe-api
# 2. Restore into a fresh database, then swap.
sudo -u postgres psql -c "CREATE DATABASE flood_prod_new OWNER flood_app;"
pg_restore -d flood_prod_new --clean database/backups/<file>.dump
sudo -u postgres psql -c "ALTER DATABASE flood_prod RENAME TO flood_prod_old;"
sudo -u postgres psql -c "ALTER DATABASE flood_prod_new RENAME TO flood_prod;"
sudo systemctl start floodsafe-api
```

### Migration verification (done 2026-09-26)

- `alembic current` → `0006 (head)` on the live database.
- `alembic upgrade head` → no-op (idempotent).
- Full DDL chain `base → head` renders cleanly offline through 0003; 0004+
  contain data migrations that require online execution (normal Alembic
  behaviour, verified by the live database reaching head).
- Known cosmetic drift: `alembic check` reports index-name differences
  (`idx_*` from the canonical schema vs `ix_*` from ORM `index=True`) and
  equivalent type spellings. Pre-existing since Phase 2, functionally
  harmless (all indexes exist and queries use them), documented here so a
  future `alembic revision --autogenerate` is not trusted blindly.

## 3. Backend environment variables

Copy `backend/.env.example` → `backend/.env` and set every value. The
variables that MUST change for production:

| Variable | Production value |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | `postgresql+psycopg2://flood_app:<password>@localhost:5432/flood_prod` |
| `SECRET_KEY` | 64+ random chars: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CORS_ORIGINS` | `https://floodsafe.example.pk` (the public frontend origin) |
| `EW_SCHEDULER_ENABLED` | `true` (single instance only — see below) |
| `LOG_FILE` | `/var/log/floodsafe-api.log` (or leave empty for stdout/journald) |

Tuning (defaults are sane): `RATE_LIMIT_PER_MINUTE=120`,
`RATE_LIMIT_AUTH_PER_MINUTE=20`, `EW_CYCLE_MINUTES=30`,
`EW_ALERT_COOLDOWN_HOURS=6`, `FCM_SERVICE_ACCOUNT_PATH` (omit → degraded
log-only push mode, fine for demo).

**Production safety checks:** with `APP_ENV=production` the app refuses to
boot if `SECRET_KEY` is still the placeholder or `CORS_ORIGINS=*`. This is
deliberate — fix `.env`, don't bypass it.

Never commit `.env`. Keep secrets in the file with `chmod 600`, owned by
the service user.

### Running the API (systemd)

```ini
# /etc/systemd/system/floodsafe-api.service
[Unit]
Description=FloodSafe Pakistan API
After=network.target postgresql.service

[Service]
User=floodsafe
WorkingDirectory=/srv/flood-risk-dss/backend
EnvironmentFile=/srv/flood-risk-dss/backend/.env
ExecStart=/srv/flood-risk-dss/backend/.venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now floodsafe-api
curl -s http://127.0.0.1:8000/health
# {"status":"ok","env":"production","model_version":"..."}
```

`--proxy-headers` is required: nginx terminates TLS and the app must see
the real client IP (rate limiting) and scheme (correct redirect URLs).

Single-instance note: the early-warning scheduler (`EW_SCHEDULER_ENABLED`)
must run on exactly one API instance, otherwise alert cycles double-run.
With `--workers 2` the scheduler lives in the lifespan of one worker
process — on multi-host deployments, run the scheduler on a dedicated
single-worker process instead.

## 4. Frontend deployment

The Next.js app (`web/`) is a standard production build. Public
(`NEXT_PUBLIC_*`) variables are baked in at build time — set them before
`next build`.

```bash
cd flood-risk-dss/web
cp .env.example .env.production.local   # then edit:
```

| Variable | Production value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `https://floodsafe.example.pk/api/v1` |
| `NEXT_PUBLIC_SITE_URL` | `https://floodsafe.example.pk` |

```bash
npm ci
npm run build        # must exit 0 — never start the server mid-build
npm start -- --port 3000   # or: pm2 / systemd unit, bound to 127.0.0.1
```

Hosting alternatives: Vercel (set the same env vars in the project
settings), or any Node 20+ host serving `next start`. The app has no
server-side secrets — everything public is `NEXT_PUBLIC_*`.

### Domain readiness checklist

- [ ] DNS A record → server IP (and AAAA if IPv6).
- [ ] TLS certificate via certbot (see nginx config below); auto-renewal
      timer enabled (`sudo certbot renew --dry-run`).
- [ ] `NEXT_PUBLIC_SITE_URL` matches the canonical domain (no trailing slash).
- [ ] `NEXT_PUBLIC_API_BASE_URL` reachable from a browser (test with curl).
- [ ] `/status` page loads and shows green checks.

## 5. nginx: TLS, reverse proxy, security headers

```nginx
# /etc/nginx/sites-available/floodsafe
upstream floodsafe_api { server 127.0.0.1:8000; }
upstream floodsafe_web { server 127.0.0.1:3000; }

server {
    listen 80;
    server_name floodsafe.example.pk;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name floodsafe.example.pk;

    ssl_certificate     /etc/letsencrypt/live/floodsafe.example.pk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/floodsafe.example.pk/privkey.pem;

    # Security headers (the API also enforces its own CORS policy).
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    # Stricter edge rate limit for auth endpoints (defence in depth;
    # the app also rate-limits internally — see §6).
    limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=120r/m;

    location /api/ {
        limit_req zone=general burst=40 nodelay;
        proxy_pass http://floodsafe_api;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /api/v1/auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://floodsafe_api;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location / {
        proxy_pass http://floodsafe_web;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo certbot --nginx -d floodsafe.example.pk   # first issuance
sudo nginx -t && sudo systemctl reload nginx
```

Because the API is served from the same domain under `/api`, browsers make
same-origin requests and CORS is effectively a non-issue in production;
`CORS_ORIGINS` still must list the domain for any direct API consumers.

## 6. Security summary

- **Secrets:** `SECRET_KEY` (JWT signing) generated with `secrets.token_urlsafe(64)`,
  stored only in `backend/.env` (chmod 600). DB role is least-privilege
  (no CREATEDB/SUPERUSER). FCM service-account JSON, if used, lives outside
  the repo with 600 permissions and is referenced by path only.
- **Boot guard:** production refuses placeholder secrets/CORS (see §3).
- **CORS:** explicit origin list with credentials in production; wildcard
  only in development (and then without credentials).
- **Rate limiting:** in-app sliding-window limiter — 120 req/min/IP general,
  20 req/min/IP on `/api/v1/auth/*`, HTTP 429 with `Retry-After`; nginx
  adds an edge layer (§5). Counters are per-process; a multi-host rollout
  should enforce the global budget at the edge.
- **Transport:** TLS 1.2+ via certbot, HSTS, HTTP→HTTPS redirect; internal
  services on loopback only.
- **Docs:** `/docs` and `/openapi.json` are disabled when `APP_ENV=production`.
- **Error handling:** unhandled exceptions return generic 500s; stack traces
  go to the log only, never to clients.
- **Backups:** encrypted-at-rest off-server copies (see §2).

## 7. Monitoring

- **Liveness:** `GET /health` → `{"status":"ok",...}` (cheap, for
  load-balancer/uptime checks).
- **Readiness:** `GET /api/v1/status` → database connectivity, prediction
  model loaded, scheduler state. Poll every 1–5 min; alert when
  `status != "ok"` or `database.ok == false`.
- **Public status page:** `/status` in the web app renders the same data
  for the public — link it in the footer (already done).
- **Logs:** timestamped application log to stdout (journald via systemd)
  and optionally `LOG_FILE`. Rotate with logrotate:

```
/var/log/floodsafe-api.log {
    daily rotate 14 compress missingok notifempty
    postrotate systemctl reload floodsafe-api >/dev/null 2>&1 || true
    endscript
}
```

- **What to alert on:** 5xx rate spike, `/api/v1/status` degraded,
  backup cron failures (`/var/log/floodsafe-backup.log`), disk usage
  > 80%, certificate expiry < 14 days (`certbot renew` timer handles this,
  but monitor it).

## 8. Deployment runbook (ordered)

1. Provision server, DNS, base packages (§1).
2. Database: role + database + PostGIS (§2).
3. Backend: venv, `.env` (all production values, §3), `alembic upgrade head`,
   verify `alembic current` → `0006 (head)`.
4. Load reference data (districts, shelters, contacts, flood history).
5. systemd unit for the API; `curl /health` → ok.
6. Frontend: production env vars, `npm ci && npm run build`, start on :3000.
7. nginx config + certbot; `nginx -t`, reload.
8. Smoke test (below). 9. Enable backups cron (§2). 10. Enable scheduler
   (`EW_SCHEDULER_ENABLED=true`, restart API) — single instance only.

### Smoke test (post-deploy)

```bash
BASE=https://floodsafe.example.pk
curl -s $BASE/api/health | grep -q '"status":"ok"' && echo "API OK"
curl -s $BASE/api/v1/status | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='ok' and d['database']['ok'], d; print('readiness OK')"
curl -s -o /dev/null -w "%{http_code}\n" $BASE/                 # 200
curl -s -o /dev/null -w "%{http_code}\n" $BASE/status           # 200
curl -s -o /dev/null -w "%{http_code}\n" $BASE/api/v1/public/situation  # 200
# Auth rate limit (expect 429s after ~20 rapid attempts):
for i in $(seq 1 25); do curl -s -o /dev/null -w "%{http_code} " -X POST $BASE/api/v1/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"x@y.z","password":"w"}'; done; echo
```

## 9. Rollback

- **Bad deploy:** `git` tag every release; roll back with
  `git checkout <previous-tag>`, rebuild, restart services. Database
  migrations are forward-only — a rollback that needs schema reversal
  restores the pre-deploy backup (§2) instead.
- **Config mistake:** the production boot guard fails fast with a clear
  message in the log; fix `.env`, `systemctl restart floodsafe-api`.

## 10. Known limitations (do not present as otherwise)

- The prediction models are district-year classifiers (seasonal aggregates);
  the API serves event-scale requests — documented in docs/ml-results.md.
- Infrastructure coordinates are sample data pending PDMA/health registries.
- `alembic check` cosmetic drift (see §2).
- Map base tiles come from OpenStreetMap; offline/low-connectivity
  environments show markers without tile imagery.
- FCM push runs in degraded log-only mode without a Firebase service
  account; the alert pipeline itself is unaffected.
