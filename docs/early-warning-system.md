# Early Warning System

How the automated flood early-warning loop works: weather ingestion →
machine learning-based prediction → alert decision → notification, plus the
citizen-report verification workflow that feeds ground truth back in.

## The cycle

```
Open-Meteo API ──▶ weather_observations ──▶ PredictionService ──▶ risk level
                                                              │
                                              ┌───────────────┴───────────────┐
                                              │ LOW → nothing                 │
                                              │ MEDIUM → advisory (watch)     │
                                              │ HIGH → emergency warning      │
                                              └───────────────┬───────────────┘
                                                              ▼
                                              alerts table ──▶ FCM push + inbox
```

**Components**

| Step | Code | Notes |
|---|---|---|
| Weather ingestion | `app/services/weather_ingestion.py`, `scripts/ingest_weather.py` | Open-Meteo current + hourly forecast, all 12 districts, idempotent upserts |
| Scheduler | APScheduler in `app/main.py` lifespan | Every `EW_CYCLE_MINUTES` (default 30); only when `EW_SCHEDULER_ENABLED=true` |
| Alert engine | `app/services/alert_engine.py` | `run_early_warning_cycle()` — weather → prediction → decision per district |
| Notifications | `app/services/notifications.py` | Firebase Admin FCM; degraded log-only mode without credentials |
| Device tokens | `POST/DELETE /mobile/device-token` | Registered per user; multicast on alert |

## Alert rule table

| Prediction | Alert issued | `alerts.severity` |
|---|---|---|
| LOW | none | — |
| MEDIUM | advisory notification | `watch` |
| HIGH | emergency warning | `emergency` |

**Cooldown.** A district does not receive a second alert at the same level
within `EW_ALERT_COOLDOWN_HOURS` (default 6). Repeated HIGH readings inside
the window are suppressed — the existing active alert stands.

**Escalation.** MEDIUM → HIGH always issues immediately, even inside the
cooldown window. The superseded advisory is deactivated (`is_active=false`)
so residents never see a stale advisory next to a live emergency.

**Provenance.** Every automated alert stores `model_version` (registry name,
e.g. `rule-based-v1`), `probability`, and `factors` (the contributing risk
factors from the prediction), so authorities can audit why an alert fired.

## Scheduler configuration

Environment variables (`backend/.env`):

| Variable | Default | Meaning |
|---|---|---|
| `EW_SCHEDULER_ENABLED` | `false` | Master switch. Keep `false` in dev/tests; enable on the production server |
| `EW_CYCLE_MINUTES` | `30` | How often the weather → prediction → alert cycle runs |
| `EW_ALERT_COOLDOWN_HOURS` | `6` | Same-level alert deduplication window |
| `EW_DEFAULT_MODEL` | `rule-based-v1` | Registry model used by the cycle (`rule-based-v1`, `mlp-v1`, …) |
| `EW_FORECAST_DAYS` | `2` | Forecast horizon fetched from Open-Meteo |
| `FCM_SERVICE_ACCOUNT_PATH` | _(unset)_ | Path to a Firebase service-account JSON |

Run one cycle manually:

```bash
cd backend
.venv/bin/python scripts/ingest_weather.py --districts Dadu Larkana   # weather only
# or drive the full cycle from a Python shell via alert_engine.run_early_warning_cycle()
```

Scheduler status (no secrets exposed): `GET /api/v1/early-warning/status`.

## FCM push notifications

**Production mode.** Set `FCM_SERVICE_ACCOUNT_PATH` to a Firebase
service-account JSON with Cloud Messaging rights. On each alert the backend
multicasts to every registered device token (`device_tokens` table).

**Degraded mode.** When no credentials are configured (development, tests),
notifications fall back to log-only: the alert payload is logged, nothing is
sent, and the cycle continues. `fcm_status()` reports the current mode.

**App wiring (production integration step).** The Flutter app has
`NotificationService.registerToken()/unregisterToken()` ready in
`lib/features/alerts/data/notification_service.dart`. Native Firebase setup
is not bundled: add `firebase_messaging` to `pubspec.yaml`,
`google-services.json` / `GoogleService-Info.plist`, request permission, and
call `registerToken(await FirebaseMessaging.instance.getToken())` after login
(and `unregisterToken()` on logout).

## Citizen reports and verification

Community reports (`POST /mobile/report-event`) carry a **category**
(`flooding`, `road_blockage`, `infrastructure_damage`, `rescue_request`,
`relief_need`, `other`) and optional photo evidence
(`POST /mobile/report-event/{id}/image` — jpg/png/webp, ≤ 5 MB, reporter or
authority only, stored under `backend/uploads/reports/`).

**Verification workflow** (authority only, `GET/PATCH /admin/reports`):

```
pending ──▶ verified ──▶ resolved
   └──▶ rejected
```

- `pending` — freshly submitted, awaiting triage.
- `verified` — confirmed by an authority user (`verified_by`, `verified_at`,
  `verification_note` recorded for audit).
- `rejected` — dismissed as invalid/duplicate, with a note.
- `resolved` — the reported situation has been handled.
- `dismissed` — legacy status from Phase 5, preserved for existing rows.

The authority **Alert Center** in the web prototype (`index.html`,
authority role) provides the triage queue with status filters,
verify/reject/resolve actions, a manual alert-creation form, and alert
history with model provenance.

## Limitations

- **Forecast uncertainty.** Open-Meteo forecasts are estimates; the cycle
  reacts to the *maximum* forecast precipitation in the next 24h, which can
  over-trigger ahead of uncertain monsoon cells.
- **Model scope.** The trained models (`mlp-v1`, `xgboost-v1`,
  `randomforest-v1`) are district-year classifiers; the operational cycle
  feeds them event-scale inputs. `rule-based-v1` is the default for the
  automated cycle because it is transparent and deterministic.
- **Reporting bias.** Citizen reports cluster where phones and volunteers
  are, not necessarily where flooding is worst; treat them as leads, not
  measurements.
- **Push targeting.** Notifications currently multicast to *all* registered
  devices. Per-district subscriptions are the next step for geo-targeted
  warnings.
- **FCM credentials.** Without a service-account JSON, push is log-only —
  the app inbox (`/mobile/alerts`) remains the reliable channel.
- **Single-instance scheduler.** APScheduler runs in-process; run exactly
  one API instance with `EW_SCHEDULER_ENABLED=true` (or move to a
  distributed scheduler) to avoid double-issuing alerts.
- **Sandboxed egress.** In this development VM, outbound HTTP goes through
  an egress proxy whose stock `no_proxy` value (containing `[::1]`) breaks
  the `requests` library. Run ingestion with a sanitized value:
  `env NO_PROXY="localhost,127.0.0.1" no_proxy="localhost,127.0.0.1" \
  .venv/bin/python scripts/ingest_weather.py`.
