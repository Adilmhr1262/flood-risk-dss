"""Data cleaning and validation for the flood risk training data.

Steps: duplicate removal, numeric coercion, domain-range validation,
median imputation of missing values, and IQR-based outlier capping.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.data_loader import BASE_FEATURES, TARGET_COLUMN

# Plausible domain ranges (feature -> (low, high)); values outside are flagged
# by validate_ranges and capped by clean(). Extra research features (e.g.
# vulnerability_index) are validated when passed via ``feature_columns``.
VALID_RANGES = {
    "rainfall_mm": (0.0, 2000.0),
    "temperature_c": (-30.0, 60.0),
    "humidity_pct": (0.0, 100.0),
    "elevation_m": (-500.0, 9000.0),
    "river_distance_km": (0.0, 1000.0),
    "slope_deg": (0.0, 90.0),
    "population_density": (0.0, 100000.0),
    "prev_flood_events": (0.0, 100.0),
    "last_severity": (0, 5),
    "vulnerability_index": (0.0, 1.0),
}


def _resolve_features(feature_columns: list[str] | None) -> list[str]:
    """Default to the nine base features when no explicit list is given."""
    return list(feature_columns) if feature_columns else list(BASE_FEATURES)


def validate_ranges(df: pd.DataFrame, feature_columns: list[str] | None = None) -> list[str]:
    """Return a list of human-readable issues for out-of-range values."""
    features = _resolve_features(feature_columns)
    issues: list[str] = []
    for col in features:
        if col not in VALID_RANGES:
            continue
        if col not in df.columns:
            issues.append(f"missing column: {col}")
            continue
        bad = df[col].dropna()
        low, high = VALID_RANGES[col]
        bad = bad[(bad < low) | (bad > high)]
        if not bad.empty:
            issues.append(
                f"{col}: {len(bad)} value(s) outside [{low}, {high}]"
                f" (min={bad.min():.2f}, max={bad.max():.2f})"
            )
    return issues


def _iqr_bounds(series: pd.Series) -> tuple[float, float]:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0 or pd.isna(iqr):
        return float(series.min()), float(series.max())
    return float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr)


def clean(df: pd.DataFrame, feature_columns: list[str] | None = None) -> pd.DataFrame:
    """Clean the training frame.

    - drops duplicate rows
    - coerces feature/label columns to numeric
    - imputes missing feature values with column medians
    - caps outliers at the IQR bounds (per column)
    - clips the label to {0, 1}

    Returns the cleaned frame plus stores nothing; use ``fit_preprocessing``
    when the imputation/capping parameters must be reused at prediction time.
    """
    features = _resolve_features(feature_columns)
    df = df.copy().drop_duplicates().reset_index(drop=True)
    for col in features + [TARGET_COLUMN]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    medians = df[features].median()
    df[features] = df[features].fillna(medians)
    for col in features:
        low, high = _iqr_bounds(df[col])
        df[col] = df[col].clip(low, high)
    if TARGET_COLUMN in df.columns:
        df[TARGET_COLUMN] = df[TARGET_COLUMN].fillna(0).astype(int).clip(0, 1)
    return df


def fit_preprocessing(df: pd.DataFrame, feature_columns: list[str] | None = None) -> dict:
    """Compute the imputation medians and IQR capping bounds from training data.

    The returned dict is serialised with the trained model so that
    single-row prediction applies identical preprocessing.
    """
    features = _resolve_features(feature_columns)
    params: dict = {"medians": {}, "bounds": {}, "features": features}
    for col in features:
        series = pd.to_numeric(df[col], errors="coerce")
        params["medians"][col] = float(series.median())
        low, high = _iqr_bounds(series.dropna())
        params["bounds"][col] = [low, high]
    return params


def apply_preprocessing(
    feature_dict: dict, params: dict, feature_columns: list[str] | None = None
) -> dict:
    """Apply training-time imputation and capping to one feature dict."""
    features = (
        list(feature_columns)
        if feature_columns
        else params.get("features", list(BASE_FEATURES))
    )
    out: dict = {}
    for col in features:
        value = feature_dict.get(col)
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = float("nan")
        if np.isnan(value):
            value = params["medians"][col]
        low, high = params["bounds"][col]
        out[col] = float(np.clip(value, low, high))
    return out
