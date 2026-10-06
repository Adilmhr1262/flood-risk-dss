# Authority Command Center (Phase W3)

The Authority Command Center is the operational interface of FloodSafe
Pakistan for disaster management officials. It is a professional disaster
operations dashboard: live situational awareness, incident lifecycle
management, resource monitoring, citizen-report triage, analytics, and an
authority-only GIS command map.

All command-center endpoints require the `authority` role. NGO, volunteer,
and public accounts receive HTTP 403. The command center contains no mock
data: every panel reads the live database, and empty states are shown until
operational records exist.

## 1. Screens

### 1.1 `/authority` — Live Command Dashboard
- **Stat cards**: active alerts, open incidents, high-risk districts, pending field reports.
- **Active alerts**: severity-graded list with deactivate actions, plus the issue-alert form (district, severity, title, message).
- **High-risk districts & latest predictions**: district, risk level, probability, model version, top contributing factors.
- **Weather status**: latest observation per district (rainfall, temperature), wettest first.
- **Open incidents** and **reports awaiting triage**: previews linking to the full modules.

### 1.2 `/authority/incidents` — Incident Management
Master-detail view. Left: filterable incident queue (All / Detected /
Verified / In response / Resolved). Right: incident detail with
- workflow stepper: **Detected → Verified → Response started → Resolved**,
- one-click advance to the next workflow state (invalid transitions return 422),
- operational notes timeline with add-note form.

Incidents can be raised manually (title, district, severity 1–5,
description) or escalated from an alert or a citizen report (`source`,
`source_id` record provenance). Reopening is not permitted: a new incident
is raised if a situation recurs, keeping the audit trail linear.

### 1.3 `/authority/resources` — Resource Management
- **Shelter monitoring**: capacity, current occupancy (progress bar),
  computed availability, operational status (`open` / `full` / `closed` /
  `maintenance`). Occupancy and status are updated inline; occupancy beyond
  capacity is rejected, and reaching capacity flips status to `full`.
- **Response teams**: rescue / medical / logistics / boat teams with district,
  size, contact, and availability status (`available` / `deployed` /
  `standby`). Create, deploy/stand-down/standby, delete.
- **Emergency infrastructure**: rescue centres, hospitals, emergency
  facilities from the infrastructure registry, with operational status.
  Rows marked "sample" are placeholder coordinates pending authoritative
  registries (documented limitation).

### 1.4 `/authority/reports` — Citizen Report Triage
Filterable queue (status × category). Each report card shows status,
priority, severity, district, and description. Authority actions:
- **Verify / Reject / Resolve** with an optional verification note and a
  priority choice — records who verified and when (auditable chain).
- **Change priority** (`low` / `medium` / `high` / `urgent`) on any report,
  including already-triaged ones.
- **Mark resolved** on verified reports.

### 1.5 `/authority/analytics` — Analytics Dashboard
- **Flood trends**: yearly event counts 2010–2024 and seasonal month
  distribution from the documented flood-event record.
- **District comparison**: total events per district and trend direction
  (mean 2017–2024 vs 2010–2016).
- **Alert history**: issued warnings, most recent first, active and
  deactivated.
- **Response statistics**: open incidents, average hours to resolve,
  incidents resolved in the last 7 days, incidents by workflow state, and
  field reports by triage state.
- Current model-prediction snapshot per district.

### 1.6 `/authority/map` — GIS Command Map
Authority-only operational GIS view with layer toggles:
- **Risk zones** (coloured by HIGH / MEDIUM / LOW),
- **Active incidents** (coloured by workflow state),
- **Field reports** (coloured by triage state),
- **Shelters** (with occupancy in the popup),
- **Response teams** (with type and status).

Incident and report layers are served by authority-only endpoints; the
public map never exposes them. On small screens the desktop sidebar is
replaced by a horizontal `CommandNav` tab strip.

## 2. User workflows

### Morning situation review
1. Open `/authority`: check stat cards (alerts, incidents, high-risk
   districts, pending reports).
2. Scan weather status for overnight rainfall; open high-risk districts
   and read top contributing factors.
3. Triage pending field reports (`/authority/reports`), verifying with a
   note and setting priorities.

### Incident handling
1. Raise an incident from `/authority/incidents`, or escalate from a
   verified report or an active alert.
2. Verify it once the field situation is confirmed; add notes as the
   situation develops.
3. Start the response: deploy teams from `/authority/resources`,
   update shelter occupancy as people arrive.
4. Resolve when the situation is over; `resolved_at` is recorded for
   response-time statistics.

### Alert broadcast
1. From the dashboard, issue a severity-graded alert for a district
   (info / watch / warning / emergency).
2. Deactivate it when the threat passes; it remains in alert history
   for the analytics record.

## 3. Data sources

| Panel | Endpoint | Table(s) |
|---|---|---|
| Active alerts | `GET /api/v1/alerts` | `alerts` |
| High-risk districts / predictions | `GET /api/v1/decision-support/summary` | `predictions`, `geographic_data` |
| Weather status | `GET /api/v1/weather/latest` | `weather_observations` |
| Incidents | `GET/POST /api/v1/incidents`, `PATCH /incidents/{id}/status`, `POST /incidents/{id}/notes`, `GET /incidents/stats` | `incidents`, `incident_notes` |
| Incident map layer | `GET /api/v1/incidents/map` | `incidents` |
| Shelters | `GET/PATCH /api/v1/resources/shelters` | `shelters` |
| Teams | `GET/POST/PATCH/DELETE /api/v1/resources/teams` | `response_teams` |
| Infrastructure | `GET /api/v1/resources/infrastructure` | `infrastructure` |
| Report triage | `GET /api/v1/admin/reports`, `PATCH /api/v1/admin/reports/{id}/verify` | `citizen_reports` |
| Report map layer | `GET /api/v1/admin/reports/map` | `citizen_reports` |
| Flood trends | `GET /api/v1/decision-support/trends` | `flood_events` |
| Alert history | `GET /api/v1/alerts` (all) | `alerts` |

Schema changes (Alembic `0006_command_center`, mirrored in
`database/schema.sql` for the test fixtures):
- `incidents` + `incident_notes` tables,
- `response_teams` table,
- `shelters.current_occupancy` + `shelters.status`,
- `citizen_reports.priority`.

## 4. Permissions

Every command-center route is guarded twice:

1. **Frontend**: `DashboardShell` with `allowedRoles={["authority"]}` redirects
   non-authority users; `proxy.ts` guards `/authority/*` server-side.
2. **Backend**: `require_role(ROLE_AUTHORITY)` on all
   `/incidents`, `/resources`, `/weather`, `/admin/reports*` endpoints.

Other roles keep their existing surfaces: the public dashboard
(`/dashboard`), the volunteer portal (`/volunteer`), and the public
FloodSafe website. Command-center data (incidents, triage queue,
operational layers) is never exposed to unauthenticated or non-authority
endpoints.

## 5. Limitations

- Incidents and response teams start empty: they are operational records
  created by authority staff, not seeded data.
- Shelter occupancy is maintained manually by authority staff; there is no
  automatic feed from shelter sites.
- Infrastructure coordinates are partly sample data pending PDMA / health
  registries (flagged in the UI).
- Weather observations depend on the early-warning ingestion pipeline
  (`scripts/ingest_weather.py`); without a run, the weather panel is empty.
