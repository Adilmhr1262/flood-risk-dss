"""Load training data for the flood risk prediction models.

Two sources are supported:

- ``"db"``  — builds the labelled training set from the live PostgreSQL
  database by joining ``flood_events`` to ``geographic_data``. Documented
  flood events become the positive class (``flooded = 1``); synthetic
  non-flood observations per district provide the negative class
  (``flooded = 0``), since the historical record only stores floods.
- a CSV path — loads a flat file with the nine base features plus a
  ``flooded`` label column (see ``ml/sample_training_data.csv``).

The nine base features are: rainfall_mm, temperature_c, humidity_pct,
elevation_m, river_distance_km, slope_deg, population_density,
prev_flood_events, last_severity.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

BASE_FEATURES = [
    "rainfall_mm",
    "temperature_c",
    "humidity_pct",
    "elevation_m",
    "river_distance_km",
    "slope_deg",
    "population_density",
    "prev_flood_events",
    "last_severity",
]
TARGET_COLUMN = "flooded"

# Exponential decay (5-year time constant) used to weight past events: recent
# floods influence prev_flood_events more than decades-old ones.
DECAY_TAU_YEARS = 5.0
RNG_SEED = 42


def load_sample_csv(path: str | Path | None = None) -> pd.DataFrame:
    """Load the bundled synthetic training CSV."""
    if path is None:
        path = Path(__file__).resolve().parent / "sample_training_data.csv"
    return pd.read_csv(path)


def _exp_decay_weight(years_ago: float) -> float:
    return float(np.exp(-years_ago / DECAY_TAU_YEARS))


def load_from_db(database_url: str) -> pd.DataFrame:
    """Build the labelled training matrix from the live database.

    Positives: every flood event with ``flood_status`` true. Per-event
    history features (``prev_flood_events``, ``last_severity``) are computed
    from earlier events of the same district, weighted by recency.
    Negatives: three synthetic non-flood observations per district with mild
    weather, labelled ``flooded = 0``.

    Returns:
        DataFrame with the nine base features and the ``flooded`` label.
    """
    engine = create_engine(database_url)
    try:
        geo = pd.read_sql(
            "SELECT id, district_name, elevation_m, river_distance_km, slope_deg,"
            " population_density_per_km2 FROM geographic_data",
            engine,
        )
        events = pd.read_sql(
            "SELECT geographic_id, event_date, rainfall_mm, temperature_c,"
            " humidity_pct, severity, flood_status FROM flood_events"
            " WHERE flood_status IS TRUE ORDER BY geographic_id, event_date",
            engine,
        )
    finally:
        engine.dispose()

    events["event_date"] = pd.to_datetime(events["event_date"])
    geo["id"] = geo["id"].astype(str)
    events["geographic_id"] = events["geographic_id"].astype(str)
    rows: list[dict] = []

    for gid, district_events in events.groupby("geographic_id"):
        g = geo.loc[geo["id"] == gid].iloc[0]
        district_events = district_events.sort_values("event_date").reset_index(drop=True)
        for i, ev in district_events.iterrows():
            prior = district_events.iloc[:i]
            prev_weighted = 0.0
            last_sev = 0
            if not prior.empty:
                years_ago = (ev["event_date"] - prior["event_date"]).dt.total_seconds() / (
                    365.25 * 24 * 3600
                )
                prev_weighted = float(np.sum([_exp_decay_weight(y) for y in years_ago]))
                last_sev = int(prior.iloc[-1]["severity"])
            rows.append(
                {
                    "rainfall_mm": ev["rainfall_mm"],
                    "temperature_c": ev["temperature_c"],
                    "humidity_pct": ev["humidity_pct"],
                    "elevation_m": g["elevation_m"],
                    "river_distance_km": g["river_distance_km"],
                    "slope_deg": g["slope_deg"],
                    "population_density": g["population_density_per_km2"],
                    "prev_flood_events": round(prev_weighted, 4),
                    "last_severity": last_sev,
                    TARGET_COLUMN: 1,
                }
            )

    # Synthetic negatives: mild-weather observations per district.
    rng = np.random.default_rng(RNG_SEED)
    for _, g in geo.iterrows():
        gid = g["id"]
        district_events = events[events["geographic_id"] == gid].sort_values("event_date")
        prev_weighted = 0.0
        last_sev = 0
        if not district_events.empty:
            ref = pd.Timestamp("2022-08-01")  # before the 2022 monsoon peak
            prior = district_events[district_events["event_date"] < ref]
            if not prior.empty:
                years_ago = (ref - prior["event_date"]).dt.total_seconds() / (
                    365.25 * 24 * 3600
                )
                prev_weighted = float(np.sum([_exp_decay_weight(y) for y in years_ago]))
                last_sev = int(prior.iloc[-1]["severity"])
        for _ in range(3):
            # Deliberately overlapping ranges: heavy rain can occur without
            # flooding (e.g. high elevation, far from river), so negatives are
            # not trivially separable from positives.
            rows.append(
                {
                    "rainfall_mm": round(float(rng.uniform(2, 130)), 1),
                    "temperature_c": round(float(rng.uniform(24, 38)), 1),
                    "humidity_pct": round(float(rng.uniform(25, 85)), 1),
                    "elevation_m": g["elevation_m"],
                    "river_distance_km": g["river_distance_km"],
                    "slope_deg": g["slope_deg"],
                    "population_density": g["population_density_per_km2"],
                    "prev_flood_events": round(prev_weighted, 4),
                    "last_severity": last_sev,
                    TARGET_COLUMN: 0,
                }
            )

    df = pd.DataFrame(rows)
    return df.reset_index(drop=True)


def load_training_data(source: str, database_url: str | None = None) -> pd.DataFrame:
    """Load a labelled training DataFrame.

    Args:
        source: ``"db"`` for the live database, otherwise a CSV file path.
        database_url: required when ``source == "db"``.
    """
    if source == "db":
        if not database_url:
            raise ValueError("database_url is required when source == 'db'")
        return load_from_db(database_url)
    return load_sample_csv(source)
