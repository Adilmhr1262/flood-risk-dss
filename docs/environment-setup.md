# Environment Variables Reference

All configuration is read from environment variables (or `backend/.env`;
see `backend/app/config.py`). Names are case-insensitive. Every variable
below has a built-in default — set explicitly the ones marked **required**
for production.

## Core

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` / `production`. Gates debug behaviour. |
| `DATABASE_URL` | `postgresql+psycopg2://flood_user:changeme@localhost:5432/flood_dss` | **Required.** SQLAlchemy URL for the application database. |
| `TEST_DATABASE_URL` | `postgresql+psycopg2://flood_user:changeme@localhost:5432/flood_dss_test` | Database used by the pytest suite. |
| `SECRET_KEY` | `change-me-to-a-long-random-secret` | **Required (production).** JWT signing key. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. Never commit. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Access-token lifetime. Production: 15–60. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh-token lifetime. |
| `CORS_ORIGINS` | `*` | **Required (production).** Comma-separated allowed origins, e.g. `https://dss.example.org`. Never `*` with credentials in production. |
| `MODEL_VERSION` | `v1.0.0-rule-based` | Fallback model version reported by `/health`. |

## Early warning cycle (Phase 6)

| Variable | Default | Description |
|---|---|---|
| `EW_SCHEDULER_ENABLED` | `false` | Set `true` to start the APScheduler early-warning cycle inside the API process. Keep `false` in tests. |
| `EW_CYCLE_MINUTES` | `30` | Interval between automated warning cycles (weather → prediction → alert decision → notify). |
| `EW_ALERT_COOLDOWN_HOURS` | `6` | Deduplication window: no repeat alert for the same district/level within this window. Escalations (MEDIUM→HIGH) always fire immediately. |
| `EW_DEFAULT_MODEL` | `mlp-v1` | Model used by the automated cycle. Aliases: `randomforest`, `xgboost`, `mlp`, legacy `rf-v1`, `rule-based-v1`. |
| `EW_FORECAST_DAYS` | `2` | Forecast horizon (days) ingested from the Open-Meteo forecast API per cycle. |
| `FCM_SERVICE_ACCOUNT_PATH` | _(unset)_ | Path to a Firebase service-account JSON. When unset or missing, push notifications run in degraded log-only mode. |

## Model registry path overrides

| Variable | Default | Description |
|---|---|---|
| `MODEL_DIR` | `<repo>/ml-models/models` | Directory holding trained model artifacts. |
| `MODEL_REGISTRY_PATH` | `<repo>/ml-models/registry.json` | Versioned model registry (configs, metrics, dataset SHA-256). |

## Example production `.env`

```bash
APP_ENV=production
DATABASE_URL=postgresql+psycopg2://flood_dss:<strong-password>@db:5432/flood_risk_dss
SECRET_KEY=<64-hex-chars>
CORS_ORIGINS=https://dss.example.org
ACCESS_TOKEN_EXPIRE_MINUTES=30
EW_SCHEDULER_ENABLED=true
EW_CYCLE_MINUTES=30
EW_ALERT_COOLDOWN_HOURS=6
EW_DEFAULT_MODEL=mlp-v1
FCM_SERVICE_ACCOUNT_PATH=/run/secrets/fcm-service-account.json
```
