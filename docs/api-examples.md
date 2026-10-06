# API Usage Examples

Base URL: `http://localhost:8000/api/v1`. All examples use `curl`.
Demo password for every demo account is `demo1234`.

## 1. Register and log in

```bash
# Register a volunteer
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"volunteer@example.org","password":"demo1234","role":"volunteer","full_name":"Test Volunteer"}'

# Log in (authority demo account)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"authority.demo@flooddss.pk","password":"demo1234"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Current user
curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"

# Refresh the access token
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token_from_login>"}'
```

## 2. Flood risk prediction

```bash
# Event-scale prediction with the best model (mlp-v1)
curl -s -X POST "http://localhost:8000/api/v1/risk/predict?model=mlp" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"district_name":"Dadu","rainfall_mm":320,"temperature_c":34.5,
       "humidity_pct":72,"elevation_m":45,"river_distance_km":8,
       "slope_deg":1.2,"population_density":410,"prev_flood_events":3,
       "last_severity":4,"vulnerability_index":0.62}'

# Compare models: model=randomforest | xgboost | mlp | rf-v1 | rule-based-v1
# Unknown model names return HTTP 200 with a rule-based fallback and an explanatory note.

# Prediction history and model info
curl -s "http://localhost:8000/api/v1/risk/predictions?limit=5" -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/v1/risk/model-info -H "Authorization: Bearer $TOKEN"
```

## 3. GIS layers

```bash
# District risk layer (GeoJSON)
curl -s "http://localhost:8000/api/v1/gis/risk-layer" -H "Authorization: Bearer $TOKEN"

# Historical flood events (filterable)
curl -s "http://localhost:8000/api/v1/gis/historical-floods?district=Dadu" -H "Authorization: Bearer $TOKEN"

# Vulnerability map and infrastructure
curl -s http://localhost:8000/api/v1/gis/vulnerability-map -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/api/v1/gis/infrastructure?type=hospital&district=Sukkur" -H "Authorization: Bearer $TOKEN"

# Shelters, emergency contacts, district boundaries
curl -s http://localhost:8000/api/v1/gis/shelters -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/v1/gis/emergency-contacts -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/v1/gis/boundaries -H "Authorization: Bearer $TOKEN"
```

## 4. Decision support

```bash
# Operational summary: high-risk districts, alerts, resources, hotspots
curl -s http://localhost:8000/api/v1/decision-support/summary -H "Authorization: Bearer $TOKEN"

# Year-wise (2010-2024) and seasonal trends
curl -s http://localhost:8000/api/v1/decision-support/trends -H "Authorization: Bearer $TOKEN"

# Resource allocations
curl -s http://localhost:8000/api/v1/decision-support/resources -H "Authorization: Bearer $TOKEN"
```

## 5. Alerts

```bash
# List active alerts
curl -s http://localhost:8000/api/v1/alerts -H "Authorization: Bearer $TOKEN"

# Create an alert (authority only)
curl -s -X POST http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"district_name":"Dadu","severity":"watch","title":"Monsoon advisory",
       "message":"Heavy rainfall expected in the next 48 hours."}'

# Deactivate an alert (authority only)
curl -s -X PATCH http://localhost:8000/api/v1/alerts/<alert_id>/deactivate \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Mobile endpoints

```bash
# Personal risk, alerts, nearby shelters (any authenticated role)
curl -s "http://localhost:8000/api/v1/mobile/my-risk?district_name=Dadu" -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/v1/mobile/alerts -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/api/v1/mobile/shelters/nearby?lat=26.73&lon=67.78&radius_km=25" \
  -H "Authorization: Bearer $TOKEN"

# File a citizen report (volunteer / public / ngo; authority gets 403)
curl -s -X POST http://localhost:8000/api/v1/mobile/report-event \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"district_name":"Dadu","lat":26.73,"lon":67.78,"severity":4,
       "category":"rescue_request","description":"Water rising near the embankment"}'
# categories: flood_water | road_blockage | rescue_request | medical_emergency

# Attach a photo to your report
curl -s -X POST http://localhost:8000/api/v1/mobile/report-event/<report_id>/image \
  -H "Authorization: Bearer $TOKEN" -F "file=@/path/to/photo.jpg"

# Register a push-notification device token
curl -s -X POST http://localhost:8000/api/v1/mobile/device-token \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"fcm_token":"<fcm-registration-token>","platform":"android"}'
```

## 7. Authority: report verification and data import

```bash
# Review citizen reports (authority only)
curl -s "http://localhost:8000/api/v1/admin/reports?status=pending" -H "Authorization: Bearer $TOKEN"

# Verify / reject / resolve a report (authority only)
curl -s -X PATCH http://localhost:8000/api/v1/admin/reports/<report_id>/verify \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"verified","note":"Confirmed by field team"}'

# Import a dataset (authority only; dry-run first)
curl -s -X POST "http://localhost:8000/api/v1/admin/import/flood_events?dry_run=true" \
  -H "Authorization: Bearer $TOKEN" -F "file=@datasets/templates/flood_events.csv"
```

Full machine-readable reference: `http://localhost:8000/docs`
(Swagger UI) and `docs/api-spec.md`.
