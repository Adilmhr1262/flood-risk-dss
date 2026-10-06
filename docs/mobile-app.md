# Mobile Application — Flood Risk DSS

Community-focused disaster management mobile app for Sindh, Pakistan.
Built with Flutter; connects to the Flood Risk DSS backend (`backend/`).

**Purpose:** help citizens and volunteers understand flood risk, receive
warnings, find emergency resources, and access safety information — including
fully offline.

**Terminology note:** this project never uses artificial-intelligence branding as a capability claim.
The app describes its predictions as *machine learning-based prediction* and
*data-driven early warning*.

## 1. Architecture

Clean architecture, pragmatic (not over-engineered):

```
lib/
├── main.dart                      # App entry, theme, MainShell (bottom nav)
├── core/
│   ├── config.dart                # API base URL (dart-define override)
│   ├── api_client.dart            # Dio client: JWT attach, refresh-on-401, error mapping
│   ├── token_storage.dart         # flutter_secure_storage: access/refresh tokens + profile
│   ├── cache_service.dart         # shared_preferences offline cache (risk, alerts, shelters, contacts, districts)
│   └── app_error.dart             # Typed errors: Unauthorized / Network / NotFound / Validation
├── features/
│   ├── auth/                      # data/auth_repository.dart, presentation/{auth_provider, splash, login, register}
│   ├── home/                      # presentation/home_screen.dart (dashboard)
│   ├── risk/                      # data/risk_repository.dart, presentation/risk_screen.dart
│   ├── map/                       # presentation/map_screen.dart (flutter_map + GeoJSON)
│   ├── alerts/                    # data/alerts_repository.dart, presentation/alerts_screen.dart
│   ├── emergency/                 # data/emergency_repository.dart, presentation/emergency_screen.dart
│   └── safety/                    # data/safety_content.dart (bundled), presentation/safety_screen.dart
└── widgets/
    └── common.dart                # LoadingView, ErrorView, EmptyView, OfflineBanner, RiskBadge
```

```
┌──────────────┐   HTTPS/JSON    ┌────────────────────────┐
│ Flutter app  │ ◄─────────────► │ FastAPI /api/v1        │
│              │  JWT bearer     │  /mobile/*, /gis/*,    │
│ Dio client   │  refresh-on-401 │  /risk/predict, /auth  │
└──────┬───────┘                 └────────────────────────┘
       │
       ├─ flutter_secure_storage → tokens (never in plain prefs)
       └─ shared_preferences    → offline cache (last risk, alerts, shelters, contacts)
```

**Auth design:** register/login issue an access + refresh JWT pair. The Dio
interceptor attaches the access token, and on a single 401 it rotates the
pair via `POST /auth/refresh` and retries once. Logout clears secure storage.
Supported roles at registration: `public`, `volunteer`, `ngo`
(`authority` accounts are created by administrators).

**Offline design:** every repository first tries the network; on a network
failure it serves the last cached payload and the UI shows an `OfflineBanner`.
The safety guide is bundled as a Dart constant — always available.

## 2. Screens

| # | Screen | File | Purpose |
|---|--------|------|---------|
| 1 | Splash | `auth/presentation/splash_screen.dart` | Disaster-management branding; restores session → app or login |
| 2 | Login / Register | `auth/presentation/{login,register}_screen.dart` | Email + password; role picker (public / volunteer / NGO) |
| 3 | Home dashboard | `home/presentation/home_screen.dart` | GPS location → nearest district risk: level, probability, last update, top factors, recommendations, quick actions |
| 4 | Risk assessment | `risk/presentation/risk_screen.dart` | District dropdown or GPS; rainfall/temperature/humidity inputs → on-demand prediction with contributing factors |
| 5 | GIS map | `map/presentation/map_screen.dart` | flutter_map: risk zones (color-coded), shelters, hospitals/rescue centres from live GeoJSON; layer toggles; tap popups; legend |
| 6 | Alerts | `alerts/presentation/alerts_screen.dart` | Active warnings with severity chips, newest first |
| 7 | Emergency | `emergency/presentation/emergency_screen.dart` | Tabs: nearby shelters (GPS, distance-sorted, tap-to-call), rescue contacts incl. Rescue 1122, flood-sighting report form |
| 8 | Safety guide | `safety/presentation/safety_screen.dart` | Offline flood-preparedness content: before / during / after, emergency kit, helplines |

Every screen implements loading, error (with retry), and empty states.

## 3. API integration

Base URL default `http://10.0.2.2:8000/api/v1` (Android emulator loopback);
override with `--dart-define=API_BASE_URL=<url>`.

| Endpoint | Method | Used by | Notes |
|---|---|---|---|
| `/auth/register` | POST | Register | `role`: public / volunteer / ngo |
| `/auth/login` | POST | Login | Returns access + refresh pair |
| `/auth/refresh` | POST | ApiClient interceptor | Silent rotation on 401 |
| `/auth/logout` | POST | AuthProvider | Stateless; local cleanup |
| `/auth/me` | GET | AuthRepository | Display name after login |
| `/mobile/my-risk?district_name=` or `?lat=&lon=` | GET | Home, Risk (GPS) | Latest assessment; 404 when none stored |
| `/risk/predict?model=` | POST | Risk assessment | On-demand prediction (default mlp-v1) |
| `/gis/districts` | GET | Risk (dropdown) | Cached offline |
| `/gis/risk-layer` | GET | Map | Color-coded risk points |
| `/gis/shelters` | GET | Map | Shelter markers |
| `/gis/infrastructure` | GET | Map | Hospitals / rescue centres |
| `/mobile/alerts` | GET | Alerts | Active warnings |
| `/mobile/shelters/nearby?lat=&lon=&radius_km=` | GET | Emergency | Geodesic distance, nearest first |
| `/mobile/emergency-contacts` | GET | Emergency | Rescue directory (+ district filter) |
| `/mobile/report-event` | POST | Emergency → Report | `{district_name, lat, lon, severity 1-5, description}` → `pending` triage |
| `/mobile/reports/mine` | GET | (profile use) | User's own reports |

## 4. User workflows

**Citizen (public):** splash → login → home shows district risk → taps
*Risk* for a fresh assessment → *Map* to see shelters → *Alerts* for warnings
→ *Emergency* to call Rescue 1122 or find the nearest shelter → *Safety guide*
read offline before monsoon.

**Volunteer:** same as citizen, plus the *Report* tab: describes observed
flooding with severity 1–5; the report (with GPS) is stored as `pending` for
authority triage via `citizen_reports`.

**NGO:** same read access; uses the report form for field observations.

## 5. Run & build

Prerequisites: Flutter SDK (stable), backend running
(`cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`).

```bash
cd mobile
flutter pub get

# Android emulator (default base URL http://10.0.2.2:8000 works)
flutter run

# Physical device on the same Wi-Fi (use the dev machine's LAN IP)
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000/api/v1

# Quality gates (verified 2026-09-26, Flutter 3.47.5)
flutter analyze        # clean — no issues
flutter test           # 7/7 pass (API client incl. 401-refresh rotation, login, safety guide)

# Web build (verifies full compilation)
flutter build web --release --dart-define=API_BASE_URL=https://your-server/api/v1
# ✓ Built build/web (verified 2026-09-26)
```

**APK:** `flutter build apk` requires the Android SDK, which is not installed
in this environment — build the APK on a machine with Android Studio, or via
Codemagic/GitHub Actions. The web build passing proves the Dart compiles.

## 6. Backend support (Phase 5)

- Alembic migration `0004`: adds `volunteer` to the `user_role` enum and
  creates the `citizen_reports` table (see `docs/database-schema.md`).
- Router `backend/app/api/v1/mobile.py` (`/mobile/*`): my-risk, alerts,
  shelters/nearby, emergency-contacts, report-event, reports/mine. All
  endpoints require authentication; `POST /mobile/report-event` is restricted
  to volunteer/public/ngo roles (authority → 403).
- Role matrix updated in `backend/README.md` (volunteer ≈ public read +
  event reporting).
- Tests: `backend/tests/test_mobile_api.py` (13 tests, incl. volunteer
  registration, role restriction, auth guards).

## 7. Limitations

- Map tiles need network (OpenStreetMap); markers/cached data work offline.
- GPS accuracy depends on the device; district matching uses centroids.
- `POST /mobile/report-event` needs connectivity (reports are not queued
  offline yet — planned enhancement).
- Infrastructure points flagged `is_sample_data` on the backend are
  illustrative until replaced by authoritative registries.
- Push notifications are not implemented; alerts are pull-based (planned:
  Firebase Cloud Messaging via the alerts API).
