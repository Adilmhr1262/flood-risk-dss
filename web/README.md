# FloodSafe Pakistan — Web Platform

Public-facing disaster management website and dashboard system for the
Flood Risk Prediction & Early Warning Decision Support System.

**Stack:** Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 ·
shadcn-style UI · Leaflet · Recharts

## Structure

```
app/
  page.tsx            Landing page (intro, features, how it works, emergency)
  login/              Sign-in (JWT against the FastAPI backend)
  register/           Registration with role selection
  dashboard/          Public dashboard (map, charts, alerts, safety guidance)
  authority/          Authority console (decision support, alert management)
  volunteer/          Volunteer portal (field reports, shelters, contacts)
components/
  ui/                 shadcn-style primitives (button, card, input, …)
  layout/             Navbar, Sidebar, DashboardShell, Footer
  MapComponent.tsx    Leaflet district risk map (live /gis/risk-layer)
  charts/             Rainfall, flood frequency, risk distribution
  RiskCard.tsx        Risk assessment card (POST /risk/predict)
  AlertCard.tsx       Flood alert card (GET /alerts)
lib/
  api/                Typed client, endpoints, and data hooks for the backend
  auth/               JWT AuthProvider, role routing, session cookies
proxy.ts              Optimistic route guard (Next.js 16 convention)
```

## Backend connection

All data comes from the existing FastAPI backend — no mock data anywhere.
Configure the base URL in `.env.local` (see `.env.example`):

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Endpoint coverage: `/auth/*`, `/dashboard/*`, `/risk/*`, `/alerts`,
`/gis/*`, `/decision-support/*`, `/mobile/report-event`, `/mobile/reports/mine`.

## Roles

| Role        | Home          | Access                                    |
| ----------- | ------------- | ----------------------------------------- |
| `public`    | `/dashboard`  | Risk map, charts, alerts, safety guidance |
| `authority` | `/authority`  | Decision support, alert management        |
| `ngo`       | `/volunteer`  | Field reports, shelters, contacts         |
| `volunteer` | `/volunteer`  | Field reports, shelters, contacts         |

## Development

```bash
npm install
npm run dev      # http://localhost:3000
npm run build
```

The backend must be running (see `../backend`, default `http://localhost:8000`).

## Terminology

Per project policy, branding, UI, code, and documentation never use the
abbreviated two-letter term for the field of automated reasoning
systems. Approved terms: *data-driven prediction*,
*machine learning-based prediction*, *risk assessment*,
*decision support system*.
