"""Feature engineering for the flood risk prediction models.

Adds four derived features that capture non-linear flood behaviour:

- rain_intensity: rainfall weighted by humidity (wet-season proxy).
  ``rainfall_mm * (humidity_pct / 100)``
- lowland_river: interaction of low elevation and river proximity.
  ``(1 / (1 + elevation_m)) * (1 / (1 + river_distance_km))``
- exposure_index: population exposure weighted by flood history.
  ``log1p(population_density) * (1 + prev_flood_events)``
- flood_history_score: recency-weighted historical event count. The
  exponential decay weighting is applied at load time (see
  ``ml.data_loader``), so this feature passes through the already-weighted
  ``prev_flood_events`` value; for static CSV sources it equals the raw
  previous-event count.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.data_loader import BASE_FEATURES, TARGET_COLUMN

ENGINEERED_FEATURES = [
    "rain_intensity",
    "lowland_river",
    "exposure_index",
    "flood_history_score",
]

MODEL_FEATURES = BASE_FEATURES + ENGINEERED_FEATURES


def engineer(
    df: pd.DataFrame, base_features: list[str] | None = None
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Add engineered features and split into X, y.

    Args:
        df: cleaned training frame with the base features and the
            ``flooded`` label column.
        base_features: base feature columns to use; defaults to the nine
            ``BASE_FEATURES`` (Phase 3 research models pass ten, adding
            ``vulnerability_index``).

    Returns:
        (X, y, feature_names): X has the base + 4 engineered features.
    """
    base = list(base_features) if base_features else list(BASE_FEATURES)
    df = df.copy()
    df["rain_intensity"] = df["rainfall_mm"] * (df["humidity_pct"] / 100.0)
    df["lowland_river"] = (1.0 / (1.0 + df["elevation_m"].clip(lower=0))) * (
        1.0 / (1.0 + df["river_distance_km"].clip(lower=0))
    )
    df["exposure_index"] = np.log1p(df["population_density"].clip(lower=0)) * (
        1.0 + df["prev_flood_events"]
    )
    df["flood_history_score"] = df["prev_flood_events"]
    feature_names = base + ENGINEERED_FEATURES
    X = df[feature_names].copy()
    y = df[TARGET_COLUMN].astype(int)
    return X, y, feature_names


def engineer_row(feature_dict: dict, base_features: list[str] | None = None) -> dict:
    """Apply the same engineered features to a single raw feature dict.

    Extra keys in ``feature_dict`` (e.g. ``vulnerability_index`` for the
    Phase 3 models) pass through untouched so the caller can select the
    model's own ``feature_names`` afterwards.
    """
    d = dict(feature_dict)
    elev = max(0.0, float(d.get("elevation_m", 0.0)))
    dist = max(0.0, float(d.get("river_distance_km", 0.0)))
    pop = max(0.0, float(d.get("population_density", 0.0)))
    d["rain_intensity"] = float(d.get("rainfall_mm", 0.0)) * (
        float(d.get("humidity_pct", 0.0)) / 100.0
    )
    d["lowland_river"] = (1.0 / (1.0 + elev)) * (1.0 / (1.0 + dist))
    d["exposure_index"] = float(np.log1p(pop)) * (1.0 + float(d.get("prev_flood_events", 0.0)))
    d["flood_history_score"] = float(d.get("prev_flood_events", 0.0))
    return d
