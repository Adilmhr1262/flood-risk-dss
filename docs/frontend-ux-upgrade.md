# FloodSafe Pakistan — Frontend UX Upgrade (Phase W5)

**Date:** 2026-09-26
**Scope:** Frontend UX/UI only. No backend logic, database schema, API, or research-methodology changes.
**Constraints honoured:** all existing live data and API connections maintained; no fake data; no unnecessary features; FloodSafe Pakistan branding kept (dark navy / white / emergency orange-red); the standing terminology rule (no mention of the prohibited technology term) is honoured everywhere.

---

## 1. What changed

### 1.1 Probability formatting fix (Task 1)
Different backend endpoints returned probability on different scales (`/gis/risk-layer` returned `82.0`; `/public/risk-check` returned `0.0733`), which produced values like `8200%`.

- New shared normalizer in `web/lib/format.ts`: `probabilityPct()` / `formatProbability()` accept either scale and return a 0–100 percentage.
- New `timeAgo()` helper for relative timestamps ("12 min ago").
- All display call sites now use the normalizer: `MapComponent`, `PublicMap`, `RiskCard`, `AlertCard`, `LiveSituationSection`, `CommandMap`, `app/authority/*`, `app/risk-check/*`.
- Grep-verified: no remaining `probability * 100` patterns in the frontend.

### 1.2 Live Flood Situation operational header (Task 2)
New component `web/components/SituationHeader.tsx`, wired into the public dashboard and the authority Command Overview.

- Dark navy operational panel with a pulsing live status indicator.
- Shows live operational state derived from current data: Emergency (any emergency alert) / Watch (any active alert or high-risk district) / Calm.
- Displays active alert count, high-risk district count, relative last-updated time, and high-risk district names.
- Action buttons: Alert Centre, Command Map.
- Clickable summary cards added beneath it on the authority dashboard: Active alerts, Open incidents, High-risk districts, Pending field reports.

### 1.3 Interactive dashboard cards (Task 3)
- `StatCard` now accepts an optional `href`: clickable cards show an arrow affordance and a lift-on-hover effect.
- Public dashboard: Active alerts → `#alerts`, High-risk areas → `/map`, Historical events → `/map?layer=history`, Current status stays informational.
- Authority dashboard: each key-figure card deep-links to its workflow page.

### 1.4 GIS upgrades (Task 4)
Public map (`PublicMap.tsx`, `/map`):
- Rich district popups: risk badge, normalized probability, main contributing factors (from the live `/public/situation` latest predictions), recommended actions, and links to risk assessment, shelters, and emergency contacts.
- Layer toggles remain: flood risk, shelters, hospitals, rescue centres, historical floods.
- Deep-link support: `/map?layer=history` pre-enables the historical layer (initialised lazily from the URL, no set-state-in-effect).

Authority command map (`CommandMap.tsx`):
- New **rainfall data** layer toggle: fetches `weatherApi.latest()` (live observations), joins to district risk centroids, sizes markers by rainfall amount, and shows rainfall / temperature / humidity / observation time in the popup. The weather fetch fails independently — the rest of the map stays usable if it errors.
- Layers: risk zones, active incidents, citizen/field reports, shelters, response teams, rainfall.

Limitation: rainfall and citizen-report layers are **not** on the unauthenticated public map because those feeds are not exposed by the existing public API surface (adding them would require backend/API changes, which are out of scope).

### 1.5 Incident timeline (Task 5)
New component `web/components/IncidentTimeline.tsx`, integrated into the authority incident detail page.

- Timeline events derived from live incident data: creation (with reported source), notes, status transitions, update time, resolution time.
- `incidentToTimeline()` maps incident + notes to a chronological event list.

### 1.6 Emergency alert cards (Task 6)
`web/components/AlertCard.tsx` rebuilt with distinct states:

- **Advisory / Watch / Warning / Emergency** severity states with coloured banners and matching badges.
- Active/Inactive status, issued time with relative age, normalized probability, monitoring/closed status, Map action, and optional incident-management action.
- Hover and entrance animations.

### 1.7 Emergency Mode (Task 7)
New `web/components/EmergencyModeView.tsx`, toggled from the public dashboard via `EmergencyModeToggle`.

- Emergency-first operational view: emergency-severity alerts, highest-risk districts, risk recommendations, live shelter listing, opt-in location to sort shelters nearest-first, rescue contacts (Rescue 1122), safety instructions.
- All content comes from live APIs; geolocation coordinates stay on-device (haversine sorting in `web/lib/geo.ts`).

### 1.8 Chart interactions (Task 8)
- `FloodFrequencyChart` rebuilt: client-side aggregation of the live `GET /gis/historical-floods` GeoJSON (52 verified events, 2010–2024) with a **district filter**, **year-range selection**, and a rich hover tooltip (per-year severity breakdown + affected population). The peak year is highlighted.
- `RainfallChart`: custom hover tooltip with mm value and rainfall-intensity reading.
- `RiskDistributionChart`: custom hover tooltip with district counts per risk level.
- District/year filters were implemented only where live per-district data exists; no fabricated data was introduced.

### 1.9 "Use My Location" public experience (Task 9)
New `web/components/MyLocationCard.tsx`, placed at the top of `/risk-check`.

- One-tap opt-in geolocation (browser permission; coordinates never leave the device).
- Matches the nearest monitored district from live risk-zone centroids and shows:
  - current risk level + normalized probability for that district (from `/public/situation`),
  - nearest shelter with distance (haversine) and tap-to-call,
  - emergency contacts (local district contacts first, fallback to national),
  - links to the full district assessment and the emergency page.
- Graceful handling of permission denial with a clear message.

### 1.10 Visual polish (Task 10)
`web/app/globals.css` and component updates:

- `fade-in-up` entrance animation, `pulse-soft` operational indicator animation.
- `card-lift` hover lift for interactive cards.
- Brand selection colour, slim theme-matched scrollbars, visible orange keyboard focus rings.
- Leaflet popups restyled to match the platform's cards (rounded, layered shadow).

---

## 2. Screens and user flows

| Screen | Route | New in W5 |
|---|---|---|
| Landing | `/` | unchanged (branding kept) |
| Public dashboard | `/dashboard` | Situation header, clickable cards, Emergency Mode toggle, rebuilt alert cards |
| Risk check | `/risk-check` | My Location card; probability fix; full district assessment |
| Flood map | `/map` | Rich district popups; `?layer=history` deep-link |
| Emergency | `/emergency` | unchanged (already had opt-in nearest-shelter sorting) |
| Learn | `/learn` | unchanged |
| Login/Register | `/login`, `/register` | unchanged |
| Authority command | `/authority` | Situation header; clickable key-figure cards |
| Incidents | `/authority/incidents` | Incident timeline on detail view |
| Resources / Reports / Analytics / Command map | `/authority/*` | Rainfall layer on command map; probability fix everywhere |
| Volunteer portal | `/volunteer` | unchanged (verified rendering) |
| Status | `/status` | unchanged |

**Key flows:**
- Citizen: `/risk-check` → "Use my location" → sees district risk, nearest shelter, contacts → "Full district assessment" or "Emergency help".
- Citizen: `/dashboard` → "Emergency Mode" → emergency-first view when a flood emergency is active.
- Authority: `/authority` → Situation header → click "High-risk districts" → `/authority/map` → toggle rainfall layer → click district → assess → manage incidents via `/authority/incidents` timeline.
- Authority: incident detail → timeline shows detection → notes → status transitions → resolution.

---

## 3. Live data sources used

| UI element | Endpoint |
|---|---|
| Situation header (public) | `GET /api/v1/public/situation` |
| Situation header (authority) | `GET /api/v1/decision-support/summary` |
| Alert cards / Emergency Mode | `GET /api/v1/alerts` (+ `/public/situation` advisories) |
| Risk probabilities | `GET /api/v1/gis/risk-layer`, `GET /api/v1/public/risk-check`, `/public/situation` |
| Flood frequency chart | `GET /api/v1/gis/historical-floods` |
| Rainfall layer (authority map) | `GET /api/v1/weather/latest` |
| District popups | `GET /api/v1/public/map/risk-zones` + `/public/situation` |
| Shelters / hospitals / rescue centres | `GET /api/v1/public/map/resources`, `GET /api/v1/public/shelters` |
| Emergency contacts | `GET /api/v1/public/emergency-contacts` |
| Incidents / notes / teams / reports | `GET /api/v1/incidents/*`, `GET /api/v1/resources/*`, `GET /api/v1/admin/reports` |

All endpoints were left unchanged; the frontend only consumes them.

---

## 4. Limitations (honest notes)

1. **Mixed probability scales** exist in the backend (`risk-layer` returns 0–100, `risk-check` returns 0–1). Fixed on the frontend with a scale-tolerant normalizer; the underlying inconsistency is a backend data contract worth unifying separately.
2. **Public map layers:** rainfall and citizen reports are not publicly exposed by the current API surface, so they remain authority-only. Adding them publicly would require API changes (out of W5 scope).
3. **Rainfall association:** weather observations are joined to district risk centroids by district name — approximate for districts without a nearby station.
4. **Weather stations:** stations are not geocoded separately; markers sit at district centroids.
5. **Map tiles:** in sandboxed/offline environments, OpenStreetMap tiles may not load; markers and controls still work. This is an environment limitation, not an app defect.
6. **Hydration:** `npm run dev` does not hydrate in this sandbox (broken HMR websocket); verification was done with production builds, as in earlier phases.

---

## 5. Verification (2026-09-26)

- `npx tsc --noEmit` — clean
- `npm run lint` — clean (one set-state-in-effect fixed via lazy URL initialisation)
- `npm run build` — clean, all 16 routes
- Production server restarted after build on `127.0.0.1:3001`
- Public tunnel routes: `/`, `/risk-check`, `/map`, `/emergency`, `/learn`, `/login`, `/status` → 200; `/dashboard`, `/authority`, `/volunteer` → 307 (login redirect, expected for anonymous)
- Demo logins through tunnel: public / authority / volunteer → 200
- Normalizer confirmed present in the production bundle
- No backend tests needed (no backend changes); last full backend run remained 150/150 from W4

## 6. Bugs found during W5

1. **8200% probability display** — caused by endpoints using mixed 0–1 / 0–100 scales. Fixed with the scale-tolerant `probabilityPct()` normalizer at every call site (grep-verified).
2. **Lint error (set-state-in-effect)** in `PublicMap` deep-link handling — fixed by lazily initialising layer state from the URL instead of an effect.
3. **TypeScript null errors** in `MyLocationCard` memoised point lists — fixed with null guards.
