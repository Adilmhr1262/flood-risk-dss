# Final Quality Review — Phase 8

Date: 2026-09-26. Scope: full project (code + documentation) after the
repository reorganization (datasets/, figures/, ml-models/ at root).
Method: test-suite run, terminology grep, cross-document claim checks,
reference/path verification. No code was changed in Phase 8.

## 1. Technical consistency — PASS

- Backend test suite re-run serially after the reorganization:
  **119/119 passed** (`cd backend && .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`).
- Model registry resolves from the new location: live
  `POST /api/v1/risk/predict?model=mlp` served by `mlp-v1` from
  `ml-models/registry.json` (verified post-reorg; dev server restarted
  2026-09-26, `/health` ok).
- Import check: `backend/ml` remains an imported package (`from ml.…`);
  only registry/artifacts moved to `ml-models/`, so no import breakage.
  `MODEL_DIR` / `MODEL_REGISTRY_PATH` env overrides exist in
  `backend/app/services/prediction_service.py`.
- Flutter: `flutter analyze` clean, `flutter test` 7/7, `flutter build web`
  succeeded (Phase 5; no mobile code touched since).
- Presentation PPTX verified by python-pptx read-back: exactly 12 slides,
  16:9, all 5 figures embedded.

## 2. Documentation consistency — PASS with notes

Cross-checked key quantitative claims across README, research paper,
project report, proposal, ml-results, data card, and module docs:

| Claim | Value | Sources agree |
|---|---|---|
| Dataset rows / positives | 180 rows, 43 positives (23.9%) | Yes — data card, ml-results, paper, report, proposal |
| Dataset SHA-256 | `4b478ea5…0418fb62` | Yes — data card, registry, paper, report |
| Train/test split | stratified 80/20 (144/36), random_state=42 | Yes |
| randomforest-v1 (acc/prec/rec/F1/ROC-AUC) | 0.8611 / 1.0000 / 0.4444 / 0.6154 / 0.9547 | Yes — ml-results, paper Table I, report, slides |
| xgboost-v1 | 0.9167 / 1.0000 / 0.6667 / 0.8000 / 0.9465 | Yes |
| mlp-v1 | 0.9444 / 1.0000 / 0.7778 / 0.8750 / 0.9630 | Yes |
| CV F1 (RF/XGB/MLP) | 0.6147±0.2073 / 0.6974±0.0935 / 0.8028±0.1110 | Yes |
| Confusion matrices | RF [[27,0],[5,4]], XGB [[27,0],[3,6]], MLP [[27,0],[2,7]] | Yes |
| Test suite | 119/119 passing | Yes — README badge matches run |
| Stack | PostgreSQL 16 + PostGIS 3.4, FastAPI, Flutter 3.47.5 | Yes |
| Demo credentials | `*.demo@flooddss.pk` / `demo1234` | Yes — install, api-examples, deployment docs |
| Figures | 5 PNGs, 300 dpi, at `figures/` | Yes — paper, slides, README |

Path checks: `docs/figures/` → `figures/` references updated in
research-paper.md, thesis-structure.md, contribution.md; `data/` →
`datasets/` in DATA_CARD.md, ml-results.md, ml-pipeline.md; no stale
`data/` or `docs/figures/` directories remain.

## 3. Terminology consistency — PASS

Banned-term grep over `.py/.md/.html/.dart/.yaml/.cff/.txt` (excluding
`.venv`, `__pycache__`, `node_modules`, `mobile/build`, `flutter-sdk`,
screenshots, scratch envs): **0 capability claims**. The only matches are
the term appearing inside the project's own terminology-rule notes
(quoted, e.g. `docs/research-paper.md:7`), which is the rule restating
itself — not a violation. "Machine Learning-Based" in the paper/report
titles is required and retained.

## 4. Research claims accuracy — PASS with open items

Every quantitative claim in the paper/report traces to a source file:
metrics → `docs/ml-results.md` + `ml-models/registry.json`; dataset facts
→ `datasets/processed/DATA_CARD.md`; alert rules → `docs/early-warning-system.md`;
GIS thresholds → `docs/gis-module.md`; report categories →
migration `0005` enum. Known-validity threats are stated in the paper's
Limitations (Section 11) and the report's Limitations chapter.

**Open items (not hidden, documented in the deliverables):**
1. Literature-review casualty/damage figures (2010: 20M affected; 2022:
   1,700+ deaths, 8M displaced, USD 30B+ damages) and GloFAS/FFWS
   characterizations were not source-verified this session — flagged in
   the report for fact-checking before submission.
2. Reference lists are IEEE-numbered but several entries carry
   `[details to be completed]` (journals, volumes, DOIs) — a citation
   pass is required before submission.
3. `EW_DEFAULT_MODEL`: resolved — `backend/.env.example` now ships
   `mlp-v1` (the best observed F1 model), matching the code default in
   `backend/app/config.py`. `rule-based-v1` remains available as a
   transparent fallback. Documented in `docs/environment-setup.md` and
   `docs/deployment-checklist.md`.
4. Screenshots re-captured against the live API on 2026-09-26:
   `screenshots/` holds six publication-grade captures (dashboard with
   live charts, risk map, decision support, alert center with alert
   history, two mobile screens), all in live mode with no demo banner.
   Note: OSM base-map tiles were unreachable from the capture
   environment, so map panes show vector overlays on a plain background;
   re-capture on a networked machine for full tile rendering.
5. Mobile FCM: token-registration API exists; native `firebase_messaging`
   wiring and `google-services.json` remain a documented integration step.
6. Suggested minimum server spec (2 vCPU/4 GB RAM) in the deployment
   checklist is an untested estimate — load testing should confirm.

## 5. Reproducibility — PASS

- Dataset: `backend/.venv/bin/python backend/ml/fetch_weather.py` →
  `backend/ml/build_dataset.py` → `datasets/processed/sindh_training_2010_2024.csv`;
  verify with `sha256sum` against `4b478ea5…0418fb62`.
- Training: `backend/.venv/bin/python backend/ml/train_phase3.py`
  reproduces the three models into `ml-models/` (deterministic seeds).
- Serving: registry + artifacts load from `ml-models/`; all 119 tests
  pass; the early-warning cycle was verified live (12/12 districts).
- Docs: `docs/installation.md` + `docs/environment-setup.md` give the
  complete setup; `CITATION.cff` cites the software and paper.

## Verdict

The project is **submission-ready as a research and portfolio package**,
subject to the open items above (fact-check literature figures, complete
the citation pass). No new features were added in Phase 8; all changes
were documentation, presentation, and repository polish.

## 6. Environment incident log — 2026-09-26

- The PostgreSQL 16 cluster went down and was found with its data
  directory reset (an earlier in-session reinstall had wiped the
  databases; only `postgres`/`template*` remained).
- Rebuilt from project sources: recreated role `flood_dss`, databases
  `flood_risk_dss` and `flood_risk_dss_test` (+ PostGIS), ran
  `alembic upgrade 0001`, loaded `database/seed.sql`, then
  `alembic upgrade head` (0002–0005).
- Verified: 12 districts / 52 flood events / 3 users; dev server healthy;
  full test suite re-run **119/119 passing**; live login and prediction
  confirmed before screenshot capture.
- Lesson: keep a `pg_dump` of the dev database under `database/` (or
  `datasets/`) before any cluster maintenance; document the
  seed-then-migrate ordering (data migrations in 0003+ expect seeded
  districts).
- **Second wipe — 2026-09-26 (~17:00 PKT):** the cluster was found down
  again with only `postgres`/`template*` databases and the `flood_dss`
  role gone entirely. Rebuilt with the same procedure via the new
  one-command script `scripts/rebuild-db.sh`; full suite re-run
  **119/119 passing**; all web-app endpoints verified live (200).
- Backup now kept at `database/backups/flood_risk_dss-2026-09-26.dump`
  (custom format, 71 KB). Re-running `scripts/rebuild-db.sh` restores a
  working database from seed + migrations in minutes.
- **Third wipe — 2026-09-26 (during Phase W2):** the cluster was found down
  a third time with the `flood_dss` role and all project databases missing.
  Rebuilt again via `scripts/rebuild-db.sh`; verified 12 districts /
  52 flood events / 3 users; full suite re-run **129/129 passing**; all
  seven public API endpoints verified live (200), including a live Dadu
  risk check (LOW, probability 0.0733).
- **Fourth wipe — 2026-09-27 (~03:40 PKT, during tunnel renewal):** the
  cluster was found with `flood_dss` role and all project databases missing
  again; logins 500'd with password-auth failure. Rebuilt via
  `scripts/rebuild-db.sh`; verified 12 districts / 52 flood events.
  Note: `volunteer@demo.pk` is not in seed.sql (created post-seed during
  Phase 5 testing), so it was re-registered via the API after the rebuild.
  All three demo logins verified live (200) through the renewed tunnel.
- **Fresh VM — 2026-09-27 (~04:44 PKT):** the sandbox machine was replaced
  (uptime reset, no PostgreSQL installed, no prior processes). Installed
  `postgresql-16` + `postgresql-16-postgis-3` via apt, started the cluster,
  rebuilt via `scripts/rebuild-db.sh` (12 districts / 52 flood events),
  re-registered `volunteer@demo.pk` (not in seed), rebuilt the frontend with
  the new tunnel URL, restarted API + web + preview proxy, and issued a new
  Pinggy tunnel. All routes and all three demo logins verified live (200).

## 7. Phase W4 production hardening — 2026-09-26

- Replaced hardcoded `CORS allow_origins=["*"]` + credentials with
  env-driven `CORS_ORIGINS` (explicit list with credentials in production;
  wildcard without credentials only in development).
- Added in-memory sliding-window rate limiting: 120 req/min/IP general,
  20 req/min/IP on `/api/v1/auth/*`, HTTP 429 with `Retry-After`.
- Added production boot guard: with `APP_ENV=production` the app refuses to
  start on the placeholder `SECRET_KEY` or `CORS_ORIGINS=*`.
- Extended monitoring: `/health` (liveness) + new `/api/v1/status`
  (readiness: database, model registry, scheduler) + public `/status` page
  in the web app (linked in the footer).
- Structured timestamped logging to stdout + optional `LOG_FILE`.
- Bug found during validation: the new rate limiter 429'd the shared test
  client, failing 41 tests + 12 errors in the full suite. Fixed by reading
  limits dynamically per request and raising budgets via a session-scoped
  test fixture (production limits unchanged). Full suite: **150/150 passing**.
- Bug found during smoke test: `/status` rendered zero badges because the
  dev `.env` CORS list lacked the `:3001` origins. Fixed in dev `.env`;
  production guidance (same-domain `/api` behind nginx) documented in
  `docs/deployment-guide.md`.
- Verified: `alembic current` → `0006 (head)`; `upgrade head` idempotent;
  full DDL chain renders offline through 0003 (0004+ data migrations need
  online execution — normal). `alembic check` cosmetic index-name drift
  (`idx_*` vs `ix_*`) is pre-existing and documented, not fixed (no schema
  churn for a cosmetic issue).
- New docs: `docs/deployment-guide.md` (server, env vars, DB, TLS/nginx,
  backups, monitoring, runbook, rollback), `docs/demo-guide.md` (12-minute
  demo script, screenshot checklist, presentation setup), plus
  `scripts/backup-db.sh` (pg_dump + 14-day rotation) and
  `scripts/demo-reset.sh` (confirmed truncate of demo operational rows).
- Terminology scan clean; TypeScript/ESLint/build clean.

## 8. Permanent hosting + Flood History Explorer — 2026-09-28

- Frontend deployed to Vercel as `floodsafe-pakistan` (permanent URL
  https://floodsafe-pakistan.vercel.app); deploy script at
  `scripts/deploy-vercel.py` (Vercel REST API, stored custom.vercel
  credential). SSO deployment protection disabled so the public can open it.
- Runtime API-URL injection: `app/layout.tsx` (server component) writes
  `window.__API_BASE_URL__` from the `API_BASE_URL` env var at request time;
  `lib/api/client.ts` `apiBase()` prefers it over the build-time
  `NEXT_PUBLIC_API_BASE_URL`. Backend tunnel changes now need only a Vercel
  env-var update, no rebuild. Backend CORS allows the Vercel origin.
- New public page `/history` (Flood History Explorer): all 52 verified
  historical flood events with district / year / severity filters, summary
  stats (events, people affected, districts hit, worst year), and per-event
  cards (severity badge, date, rainfall, affected population, damage
  description, source). Read-only over `/public/historical-floods`; no
  backend changes. Nav link added ("Flood history").
- Verified: `tsc --noEmit` clean, ESLint clean, production build clean
  (20 routes incl. `/history`), Vercel deployment READY, `/history` 200
  live with correct heading, logins 200 through the tunnel with the Vercel
  origin.
