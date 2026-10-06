"""v1 rule-based flood risk scoring engine.

A deterministic, data-driven risk assessment. Each of the nine input features is
normalised to a 0-1 risk contribution and combined with fixed weights that sum
to 1.0. This transparent baseline serves as the decision-support reference
while the trained machine learning models (ml/pipeline.py) are validated.

Weights (sum = 1.0):
    rainfall_mm        0.25
    river_distance_km  0.18  (inverse: closer river = higher risk)
    elevation_m        0.15  (inverse: lower elevation = higher risk)
    prev_flood_events  0.12
    humidity_pct       0.08
    slope_deg          0.08  (inverse: flatter terrain = higher risk)
    population_density 0.07
    temperature_c      0.04
    last_severity      0.03
"""

from __future__ import annotations

import math

MODEL_VERSION = "v1.0.0-rule-based"

LOW_THRESHOLD = 0.33
MEDIUM_THRESHOLD = 0.66
FACTOR_INCLUDE_THRESHOLD = 0.5  # normalised feature value at/above this is "significant"

WEIGHTS: dict[str, float] = {
    "rainfall_mm": 0.25,
    "river_distance_km": 0.18,
    "elevation_m": 0.15,
    "prev_flood_events": 0.12,
    "humidity_pct": 0.08,
    "slope_deg": 0.08,
    "population_density": 0.07,
    "temperature_c": 0.04,
    "last_severity": 0.03,
}


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


# --- normalisation: raw feature -> 0-1 risk contribution ---------------------

def norm_rainfall(mm: float) -> float:
    """200 mm+ rainfall saturates at maximum contribution."""
    return _clip(mm / 200.0)


def norm_river_distance(km: float) -> float:
    """Inverse: areas within ~0 km of a river contribute most; beyond 10 km, none."""
    return _clip(1.0 - km / 10.0)


def norm_elevation(m: float) -> float:
    """Inverse: sea-level terrain contributes most; above 500 m, none."""
    return _clip(1.0 - m / 500.0)


def norm_prev_flood_events(count: float) -> float:
    """5 or more previous events saturate at maximum contribution."""
    return _clip(count / 5.0)


def norm_humidity(pct: float) -> float:
    """Risk rises once humidity passes ~40%; saturates at 100%."""
    return _clip((pct - 40.0) / 60.0)


def norm_slope(deg: float) -> float:
    """Inverse: flat ground (<1 deg) contributes most; steeper than 15 deg, none."""
    return _clip(1.0 - deg / 15.0)


def norm_population_density(density: float) -> float:
    """Log-scaled: exposure grows with density; ~10,000 per sq km saturates."""
    return _clip(math.log10(1.0 + density) / 4.0)


def norm_temperature(c: float) -> float:
    """Risk rises above 20 C; saturates at 40 C (snowmelt / monsoon heat proxy)."""
    return _clip((c - 20.0) / 20.0)


def norm_last_severity(severity: int) -> float:
    """Severity scale 0=None, 1=Minor, 2=Moderate, 3=Severe, 4=Very severe, 5=Catastrophic (matches flood_events.severity)."""
    return _clip(severity / 5.0)


NORMALISERS = {
    "rainfall_mm": norm_rainfall,
    "river_distance_km": norm_river_distance,
    "elevation_m": norm_elevation,
    "prev_flood_events": norm_prev_flood_events,
    "humidity_pct": norm_humidity,
    "slope_deg": norm_slope,
    "population_density": norm_population_density,
    "temperature_c": norm_temperature,
    "last_severity": norm_last_severity,
}

# Human-readable factor labels shown when a feature is significant.
FACTOR_LABELS = {
    "rainfall_mm": "Heavy rainfall",
    "river_distance_km": "River proximity",
    "elevation_m": "Low elevation",
    "prev_flood_events": "Recurrent flooding history",
    "humidity_pct": "High humidity",
    "slope_deg": "Flat terrain",
    "population_density": "Dense population exposure",
    "temperature_c": "High temperature",
    "last_severity": "Past severe flooding",
}

RECOMMENDATIONS = {
    "LOW": [
        "Stay informed through official flood alerts",
        "Keep basic emergency supplies available",
        "Know the location of your nearest shelter",
    ],
    "MEDIUM": [
        "Monitor weather forecasts and river levels",
        "Clear drainage channels around your property",
        "Keep emergency supplies and documents ready",
        "Review your household emergency plan",
    ],
    "HIGH": [
        "Prepare evacuation plans",
        "Monitor water levels",
        "Contact emergency services",
        "Move to designated shelters if advised by authorities",
    ],
}


def risk_level(probability: float) -> str:
    """Classify a 0-1 probability: LOW < 0.33, MEDIUM < 0.66, else HIGH."""
    if probability < LOW_THRESHOLD:
        return "LOW"
    if probability < MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "HIGH"


def assess_risk(features: dict[str, float]) -> dict:
    """Run the full assessment over the nine normalised features.

    Args:
        features: mapping of the nine feature names to raw values.

    Returns:
        dict with probability (0-1), risk_level, main_factors (list of
        human-readable labels), recommendations (list of strings),
        weighted contributions per feature, and the model version.
    """
    normalised = {k: NORMALISERS[k](features.get(k, 0.0)) for k in WEIGHTS}
    contributions = {k: normalised[k] * WEIGHTS[k] for k in WEIGHTS}
    probability = _clip(sum(contributions.values()))

    # Significant factors, ordered by weighted contribution, highest first.
    main_factors = [
        FACTOR_LABELS[k]
        for k in sorted(contributions, key=contributions.get, reverse=True)
        if normalised[k] >= FACTOR_INCLUDE_THRESHOLD
    ]

    level = risk_level(probability)
    return {
        "probability": round(probability, 4),
        "risk_level": level,
        "main_factors": main_factors,
        "recommendations": list(RECOMMENDATIONS[level]),
        "contributions": {k: round(v, 4) for k, v in contributions.items()},
        "model_version": MODEL_VERSION,
    }
