"""Build the Phase 3 research training dataset: Sindh flood risk 2010-2024.

Grain: one row per district-year (12 districts x 15 years = 180 rows).

DESIGN DECISION (why district-year, not district-event-window):
  Floods in Sindh are monsoon-season phenomena, so the hydrologically honest
  unit is the monsoon year. District-event-window rows would need exact
  event-day weather for every historical flood (unavailable for most rows)
  and would leave no honest negative class. District-year rows give a real
  negative class -- district-years with no documented flood event -- and let
  the model learn from monsoon-season aggregates, which is also how the
  prediction API is used (a district's current monsoon outlook).

Label definition:
  flooded = 1 if at least one verified flood event is recorded for the
  district in that calendar year (see datasets/raw/sindh_flood_events_2010_2024.csv),
  else 0.  severity = maximum verified severity that year (0 when none).

Known limitation (documented, not hidden): the negative class means "no
*flood event documented in the compiled sources*", not "no flood occurred".
Reporting is biased toward catastrophic, deadly events; minor urban flooding
is under-reported, especially before ~2015. See DATA_CARD.md.

Feature mapping to the nine base model features:
  rainfall_mm      = monsoon (Jun-Sep) precipitation sum, mm (ERA5)
  temperature_c    = monsoon mean of daily mean temperature, C (ERA5)
  humidity_pct     = monsoon mean of daily mean relative humidity, % (ERA5)
  elevation_m, river_distance_km, slope_deg, population_density = static
  prev_flood_events = count of verified events in the same district in
                      strictly earlier years
  last_severity     = max severity of verified events in strictly earlier
                      years (0 when none)
  vulnerability_index (10th feature) = documented composite, static per
                      district (see DATA_CARD.md):
                      0.5 * minmax(log1p(population_density))
                    + 0.3 * minmax(total verified events 2010-2024)
                    + 0.2 * minmax(1 / (1 + river_distance_km))
                      (density is log-transformed: it spans 160-3650/km2)

Usage:
    .venv/bin/python backend/ml/build_dataset.py
Writes datasets/processed/sindh_training_2010_2024.csv and prints a summary.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # backend/
PROJECT = ROOT.parent
RAW = PROJECT / "datasets" / "raw"
PROCESSED = PROJECT / "datasets" / "processed"

MONSOON_MONTHS = (6, 7, 8, 9)
YEARS = list(range(2010, 2025))


def load_weather(district: str) -> pd.DataFrame:
    """Daily ERA5 frame for one district from the cached Open-Meteo JSON."""
    path = RAW / "weather" / f"{district}.json"
    data = json.loads(path.read_text())
    d = data["daily"]
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(d["time"]),
            "precip_mm": pd.to_numeric(d["precipitation_sum"], errors="coerce"),
            "tmax_c": pd.to_numeric(d["temperature_2m_max"], errors="coerce"),
            "tmin_c": pd.to_numeric(d["temperature_2m_min"], errors="coerce"),
            "humidity_pct": pd.to_numeric(
                d["relative_humidity_2m_mean"], errors="coerce"
            ),
        }
    )
    df["tmean_c"] = (df["tmax_c"] + df["tmin_c"]) / 2.0
    return df


def minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(0.5, index=s.index)
    return (s - lo) / (hi - lo)


def main() -> None:
    static = pd.read_csv(RAW / "district_static.csv")
    events = pd.read_csv(RAW / "sindh_flood_events_2010_2024.csv")
    events["event_date"] = pd.to_datetime(events["event_date"])
    events["year"] = events["event_date"].dt.year

    districts = list(static["district_name"])
    assert set(districts) == set(events["district_name"].unique()), (
        "event districts must be a subset of the study districts: "
        f"{set(events['district_name'].unique()) - set(districts)}"
    )

    # --- vulnerability composite (static per district) ---
    # Population density is log-transformed before normalisation: it spans an
    # order of magnitude (160-3650 /km2) and would otherwise saturate the
    # exposure component on Karachi alone.
    log_dens = np.log1p(static.set_index("district_name")["population_density_per_km2"])
    ev_counts = events.groupby("district_name").size().reindex(districts).fillna(0)
    vuln = (
        0.5 * minmax(log_dens)
        + 0.3 * minmax(ev_counts)
        + 0.2 * minmax(1.0 / (1.0 + static.set_index("district_name")["river_distance_km"]))
    ).round(4)
    static = static.set_index("district_name")
    static["vulnerability_index"] = vuln

    rows = []
    for district in districts:
        w = load_weather(district)
        w["year"] = w["date"].dt.year
        w["month"] = w["date"].dt.month
        dev = events[events["district_name"] == district]
        st = static.loc[district]
        for year in YEARS:
            wy = w[w["year"] == year]
            mon = wy[wy["month"].isin(MONSOON_MONTHS)]
            prior = dev[dev["year"] < year]
            in_year = dev[dev["year"] == year]
            rows.append(
                {
                    "district_name": district,
                    "year": year,
                    # base features (names match ml.data_loader.BASE_FEATURES)
                    "rainfall_mm": round(float(mon["precip_mm"].sum()), 1),
                    "temperature_c": round(float(mon["tmean_c"].mean()), 2),
                    "humidity_pct": round(float(mon["humidity_pct"].mean()), 1),
                    "elevation_m": float(st["elevation_m"]),
                    "river_distance_km": float(st["river_distance_km"]),
                    "slope_deg": float(st["slope_deg"]),
                    "population_density": float(st["population_density_per_km2"]),
                    "prev_flood_events": int(len(prior)),
                    "last_severity": int(prior["severity"].max()) if len(prior) else 0,
                    "vulnerability_index": float(st["vulnerability_index"]),
                    # labels
                    "flooded": int(len(in_year) > 0),
                    "severity": int(in_year["severity"].max()) if len(in_year) else 0,
                    # provenance / contextual columns (not model inputs)
                    "rainfall_annual_mm": round(float(wy["precip_mm"].sum()), 1),
                    "rainfall_max_daily_mm": round(float(wy["precip_mm"].max()), 1),
                    "n_events_in_year": int(len(in_year)),
                }
            )

    df = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / "sindh_training_2010_2024.csv"
    df.to_csv(out, index=False)

    pos = int(df["flooded"].sum())
    print(f"wrote {out} ({len(df)} rows)")
    print(f"positive rows (flooded=1): {pos} ({pos/len(df):.1%})")
    print("events per year:", dict(sorted(df.groupby("year")["flooded"].sum().items())))
    print("\nvulnerability_index by district:")
    for d in districts:
        print(f"  {d:<16}{static.loc[d, 'vulnerability_index']:.4f}")


if __name__ == "__main__":
    main()
