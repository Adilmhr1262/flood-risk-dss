# Data Card — Sindh Flood-Risk Training Dataset (Phase 3)

**File:** `datasets/processed/sindh_training_2010_2024.csv`
**Built by:** `backend/ml/build_dataset.py` (reproducible; re-run any time)
**Version:** v1.0 — built 2026-09-26

## Study area and period

- **Area:** 12 districts of Sindh Province, Pakistan — Badin, Dadu, Ghotki,
  Hyderabad, Jacobabad, Karachi, Larkana, Shikarpur, Sukkur, Thatta —
  plus Dera Ghazi Khan and Rajanpur (Punjab districts on the Sindh border,
  included because Indus riverine flooding crosses the provincial boundary;
  flagged as non-Sindh in analysis).
- **Period:** 2010-01-01 to 2024-12-31 (15 monsoon years).
- **Grain:** one row per district-year → **180 rows**, of which **43 (23.9%)**
  are positive (at least one verified flood event that year).

## Sources

| Data | Source | Access |
|---|---|---|
| Flood events (43 district-level records, 2010–2022) | NDMA situation reports, PDMA Sindh Flood Impact Report 2022, WHO worst-affected district lists, Pakistan Met Department records, Dawn/ReliefWeb/OCHA/IFRC situation reports | Curated in `datasets/raw/sindh_flood_events_2010_2024.csv`; every row carries its own `source` citation and `source_url` |
| Daily weather (precipitation, temperature, humidity) | ERA5 reanalysis via the Open-Meteo archive API (2010-01-01–2024-12-31, daily) | Cached raw JSON in `datasets/raw/weather/<district>.json` |
| Elevation, river distance, slope, population density | Project `geographic_data` table (snapshot in `datasets/raw/district_static.csv`) | Static per district (see limitations) |

## Feature definitions

| Feature | Definition |
|---|---|
| `rainfall_mm` | Monsoon-season (Jun–Sep) precipitation sum, mm (ERA5 `precipitation_sum`) |
| `temperature_c` | Monsoon-season mean of daily mean temperature, °C (ERA5) |
| `humidity_pct` | Monsoon-season mean of daily mean relative humidity, % (ERA5) |
| `elevation_m` | District mean elevation above sea level, m (static) |
| `river_distance_km` | Distance to nearest major river (Indus), km (static) |
| `slope_deg` | Mean terrain slope, degrees (static) |
| `population_density` | Persons per km² (static; time-invariant proxy — see limitations) |
| `prev_flood_events` | Count of verified flood events in the same district in strictly earlier years |
| `last_severity` | Maximum severity (1–5) of verified events in strictly earlier years; 0 if none |
| `vulnerability_index` | Composite, static per district (formula below) |
| `flooded` (label) | 1 if ≥1 verified flood event in the district-year, else 0 |
| `severity` (label) | Maximum verified severity in the district-year; 0 if none |

**Vulnerability composite** (provisional — documented, not validated against
independent socioeconomic data):

```
vulnerability_index = 0.5 * minmax(log1p(population_density))
                    + 0.3 * minmax(total verified events 2010-2024 in district)
                    + 0.2 * minmax(1 / (1 + river_distance_km))
```

Components capture exposure (people in harm's way), historical susceptibility
(past floods predict future floods), and physical exposure (Indus proximity).
Density is log-transformed because it spans an order of magnitude
(160–3,650/km²); without the transform Karachi alone saturates the component.
Weights are a reasoned prior (exposure dominant), not fitted.

**Contextual columns** (provenance, not model inputs): `district_name`,
`year`, `rainfall_annual_mm`, `rainfall_max_daily_mm`, `n_events_in_year`.

## Design decision: district-year grain

Floods in Sindh are monsoon-season phenomena, so the honest analytical unit
is the monsoon year. The alternative (one row per district-event window)
would require exact event-day weather for every historical flood — unavailable
for most rows — and would leave no honest negative class. District-year rows
give a real negative class (district-years with no documented flood) and match
how the prediction API is used (a district's current monsoon outlook).

## Known limitations and biases

1. **Reporting bias.** The negative class means "no *documented* flood", not
   "no flood". Sources systematically under-report minor urban flooding and
   pre-2015 events. Positive rows skew toward catastrophic, deadly events.
2. **No event before 2010 in history features.** `prev_flood_events` for 2010
   rows is 0 by construction; earlier floods (e.g. 1990s) are not modelled.
3. **Static population density.** Uses a single per-district value across
   15 years; ignores urbanisation (notably Karachi's growth).
4. **ERA5 reanalysis, not station data.** Gridded reanalysis smooths extreme
   local downpours; district values are bilinear estimates at the centroid.
5. **Severity is ordinal and source-dependent.** Assigned 1–5 from narrative
   reports (deaths, displacement, inundation area), not a calibrated scale.
6. **Small sample.** 180 rows / 43 positives is modest; metrics (especially
   ROC-AUC) have wide confidence bands. Cross-validation is reported.
7. **Vulnerability composite is provisional.** Weights are reasoned, not
   fitted or externally validated; it must not be read as a measured
   socioeconomic index.

## Reproduce

```bash
cd ~/workspace/flood-risk-dss
backend/.venv/bin/python backend/ml/fetch_weather.py   # fills data/raw/weather/
backend/.venv/bin/python backend/ml/build_dataset.py   # writes data/processed/sindh_training_2010_2024.csv
sha256sum data/processed/sindh_training_2010_2024.csv
```
