# FloodSafe Pakistan — Demo Guide

How to present the platform live: the scripted workflow, the screenshots
to capture, and the presentation environment setup. Assumes the deployment
in docs/deployment-guide.md is up, or the local dev pair
(API :8000 + web :3000/:3001).

## 1. Presentation environment setup (15 min before)

1. Reset operational data from any previous demo:
   `scripts/demo-reset.sh` (asks for `RESET` confirmation; keeps all seed
   and reference data).
2. Start services and confirm green:
   - `curl -s localhost:8000/health` → `{"status":"ok",...}`
   - Open `/status` in the browser — all four components Operational.
3. Prepare three browser profiles/windows (or one normal + two private):
   - **Public** (no login)
   - **Authority** — log in as the authority demo account
   - **Volunteer** — log in as the volunteer demo account
4. Check the map tiles load (needs internet — OpenStreetMap). If offline,
   markers and panels still work; say so once and move on.
5. Set the browser zoom to 100%, hide bookmarks bar, close other tabs.

Demo accounts (create once via `/register`, keep credentials in the
presenter's notes — never on slides):

| Role | Purpose |
|---|---|
| authority | Command Center: incidents, resources, reports, analytics, GIS map |
| volunteer | Volunteer portal + mobile-app screens |
| public | Risk check, emergency page (no login needed) |

## 2. Demo workflow (12-minute script)

**0:00 — Landing (public).** Open `/`. One line: "FloodSafe Pakistan is a
data-driven flood risk prediction and early warning decision support
system for authorities, NGOs, volunteers, and the public."

**0:01 — Risk check (public).** `/risk-check` → type "Dadu" → show the
risk level, contributing factors, and recommended actions. Point out the
numbers come from the trained models (F1 0.875 MLP), not mock data.

**0:03 — Live map (public).** `/map` → toggle risk zones, shelters, field
reports. Zoom to a high-risk district.

**0:05 — Emergency page (public).** `/emergency` → allow location →
shelters sort nearest-first with km badges. Mention: location never leaves
the device.

**0:06 — Authority Command Center.** Switch window. `/authority` dashboard:
live KPIs, incident list. Create an incident:
`/authority/incidents` → New → fill district/severity → walk the workflow
Detected → Verified → Response Started (show the forward-only rule:
"resolved incidents can't be reopened — recurrence needs a new incident").

**0:08 — Resources + reports.** `/authority/resources` → deploy a response
team; `/authority/reports` → triage a citizen report (verify it).

**0:09 — Analytics + GIS command map.** `/authority/analytics` → trends;
`/authority/map` → layers (risk zones, incidents, reports, shelters,
teams).

**0:10 — Volunteer + mobile.** Volunteer portal: submit a field report.
Mention the Flutter app (8 screens, same backend).

**0:11 — Status.** `/status` → all green. Close: "Monitoring, backups, and
rate limiting are production-ready — see docs/deployment-guide.md."

## 3. Screenshot checklist

Capture at 1440×900, light mode, real data only:

- [ ] `/` — landing hero
- [ ] `/risk-check` — district result with factors
- [ ] `/map` — risk zones + shelters visible
- [ ] `/emergency` — nearest shelters with km badges
- [ ] `/authority` — dashboard KPIs
- [ ] `/authority/incidents` — workflow states visible
- [ ] `/authority/resources` — teams + shelters
- [ ] `/authority/reports` — triage queue
- [ ] `/authority/analytics` — trend charts
- [ ] `/authority/map` — command map with layers
- [ ] `/volunteer` — volunteer portal
- [ ] `/status` — all operational
- [ ] `/learn` — safety guide (optional)
- [ ] Mobile: home, risk, map, alerts screens (Flutter web build)

Save under `screenshots/` (already in repo layout). Recapture the map
shots on a network where OSM tiles load — earlier captures have a grey
base map.

## 4. After the demo

- Run `scripts/demo-reset.sh` again so the next presenter starts clean.
- Note any bug or awkward moment in docs/quality-review.md — demos are
  the best QA this project gets.
