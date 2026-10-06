# FloodSafe Pakistan — Public Web Experience

Phase W2 deliverable. The public FloodSafe Pakistan website lets any citizen —
no account, no login — check flood risk, explore the risk map, find emergency
help, and learn flood safety. It consumes only the unauthenticated
`/api/v1/public/*` API surface and contains zero mock data: every number on
screen comes from the live PostgreSQL/PostGIS database and the trained
prediction service.

> **Terminology rule.** This project never applies the artificial-intelligence label as a capability claim in
> branding, UI, code, comments, API responses, or documentation. Public copy
> uses "data-driven prediction", "machine learning-based prediction", "risk
> assessment", "early warning", and "decision support system".

## Routes

| Route | Purpose | Auth |
|---|---|---|
| `/` | Landing page with Live Situation section | none |
| `/risk-check` | District flood-risk self-assessment | none |
| `/map` | Public GIS: risk zones, shelters, hospitals, rescue centres, historical floods | none |
| `/emergency` | Hotlines, emergency contact directory, shelter finder | none |
| `/learn` | Flood safety guide (before / during / after) | none |
| `/login`, `/register` | Existing account flows | none (entry) |
| `/dashboard`, `/authority`, `/volunteer` | Existing role consoles (unchanged) | required |

Anonymous visitors are never bounced to `/login`. The `AuthProvider` only
redirects to `/login` from protected routes (`/dashboard`, `/authority`,
`/volunteer`); on public pages an expired or absent session simply stays
anonymous. (A pre-W2 bug redirected *every* anonymous page load to `/login`
because `authApi.me()` was called unconditionally — fixed in W2.)

## User flows

### 1. Check my district's risk (no login)
1. Visitor opens `/risk-check` (or clicks "Check my district" on the homepage).
2. Selects a district from the dropdown (populated from
   `GET /public/districts`).
3. Clicks "Check risk" → `GET /public/risk-check?district_name=…` runs the
   stored district attributes + latest weather through the prediction service
   (Random Forest `rf-v1`) and returns probability, category, contributing
   factors, and recommendations.
4. The page renders a risk gauge, "what this means", contributing factors,
   safety recommendations, the inputs used, and the assessment timestamp.
5. Deep link: `/risk-check?district=Dadu` pre-selects and auto-runs.

Anonymous checks are deliberately **not** persisted server-side.

### 2. Explore the risk & relief map
1. Visitor opens `/map`.
2. `GET /public/map/risk-zones` draws per-district risk circles (green → red).
3. Layer toggles add shelters (`?type=shelter`, served from the **shelters**
   registry table), hospitals, rescue centres, and historical flood events.
4. District search recentres the map; tapping a marker shows a detail popup.
5. Shelter/facility points flagged `is_sample_data` carry an on-map disclaimer
   to confirm illustrative locations with local authorities before travelling.

### 3. Get help in an emergency
1. Visitor opens `/emergency`.
2. Three tap-to-call cards: **Rescue 1122**, **PDMA Sindh 1736**, **National
   emergency 911** (`tel:` links).
3. Live emergency-contact directory (`GET /public/emergency-contacts`),
   filterable by district, each row with a call button.
4. Shelter finder (`GET /public/map/resources?type=shelter`):
   - District filter, or
   - **"Use my location"** — opt-in browser geolocation; shelters are sorted
     nearest-first client-side with haversine distance ("≈ 11.6 km away")
     computed from their stored coordinates. No location ever leaves the
     device; denied/unavailable geolocation falls back to district order.

### 4. Learn flood safety
`/learn` — tabbed guide (Before / During / After a flood) with household-level
preparedness checklists. Static content, cross-links to the risk checker and
the relief map.

## Public API usage

Base URL: `http://localhost:8000/api/v1`. No token required.

```bash
# Live situation (homepage)
curl -s http://localhost:8000/api/v1/public/situation

# Risk self-check for a district
curl -s "http://localhost:8000/api/v1/public/risk-check?district_name=Dadu"

# Map layers
curl -s http://localhost:8000/api/v1/public/map/risk-zones
curl -s "http://localhost:8000/api/v1/public/map/resources?type=shelter"
curl -s "http://localhost:8000/api/v1/public/map/resources?type=hospital&district_name=Larkana"

# Emergency directory and districts
curl -s http://localhost:8000/api/v1/public/emergency-contacts
curl -s http://localhost:8000/api/v1/public/districts
curl -s "http://localhost:8000/api/v1/public/historical-floods?district_name=Dadu"
```

Response shapes mirror the authenticated GIS layers (GeoJSON
FeatureCollections) so the web client, the Flutter app, and authority consoles
share one data contract. The public situation summary reuses the same
`build_situation_summary()` as the authority decision-support endpoint, minus
restricted resource-allocation detail.

## Frontend implementation notes

- `web/lib/api/public.ts` — typed unauthenticated client + shared types
  (`GeoJSONFeatureCollection`, `PublicSituation`, `RiskCheckResult`, …).
- `web/components/LiveSituationSection.tsx` — homepage section with skeleton
  loaders, error fallback, and empty states (never blank).
- `web/components/PublicMap.tsx` — Leaflet map; `ssr: false` via
  `next/dynamic` (Leaflet needs `window`).
- `web/app/risk-check/page.tsx`, `web/app/map/page.tsx`,
  `web/app/emergency/page.tsx`, `web/app/learn/page.tsx`.
- `web/components/layout/Navbar.tsx` — public links + mobile hamburger menu;
  on small screens the header collapses to compact logo + menu + Create
  account, with Sign in inside the menu.
- Sandbox note: `npm run dev` does not hydrate in this environment (broken
  HMR websocket); verify with `npm run build` + `npx next start`. OSM map
  tiles are unreachable from this sandbox, so the base map renders grey here
  while markers, popups, and controls all work — tiles load on a normal
  network.

## Verification (2026-09-26)

- Backend: `pytest tests/` — **129/129 passed** (incl. 10 public-API tests;
  anonymous access plus a shelter-registry regression test).
- `npx tsc --noEmit` — clean. `npm run lint` — clean. `npm run build` — clean.
- Playwright (local Chromium, production build): all five public routes return
  200 and render with live data at 1440×900 and 390×844; mobile menu opens;
  `/risk-check?district=Dadu` auto-runs an assessment (7%, LOW); shelter
  finder lists 6 real shelters; "Use my location" sorts nearest-first with
  distances; no console errors, no failed requests.
