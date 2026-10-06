"""Tests for the v1 rule-based risk engine."""

import pytest

from app.services import risk_engine
from app.services.risk_engine import assess_risk, risk_level

DADU_LIKE = {
    "rainfall_mm": 180.0,
    "temperature_c": 34.0,
    "humidity_pct": 92.0,
    "elevation_m": 45.0,
    "river_distance_km": 1.2,
    "slope_deg": 1.5,
    "population_density": 950.0,
    "prev_flood_events": 4,
    "last_severity": 3,
}

SAFE = {
    "rainfall_mm": 5.0,
    "temperature_c": 22.0,
    "humidity_pct": 45.0,
    "elevation_m": 800.0,
    "river_distance_km": 40.0,
    "slope_deg": 12.0,
    "population_density": 50.0,
    "prev_flood_events": 0,
    "last_severity": 0,
}


def test_weights_sum_to_one():
    assert sum(risk_engine.WEIGHTS.values()) == pytest.approx(1.0)


def test_probability_within_bounds():
    for features in (DADU_LIKE, SAFE):
        result = assess_risk(features)
        assert 0.0 <= result["probability"] <= 1.0


def test_level_thresholds():
    assert risk_level(0.0) == "LOW"
    assert risk_level(0.329) == "LOW"
    assert risk_level(0.33) == "MEDIUM"
    assert risk_level(0.659) == "MEDIUM"
    assert risk_level(0.66) == "HIGH"
    assert risk_level(1.0) == "HIGH"


def test_dadu_like_high_risk():
    result = assess_risk(DADU_LIKE)
    assert result["risk_level"] == "HIGH"
    assert result["probability"] >= 0.66
    assert "Heavy rainfall" in result["main_factors"]
    assert "Low elevation" in result["main_factors"]
    assert "River proximity" in result["main_factors"]
    assert "Prepare evacuation plans" in result["recommendations"]
    assert "Monitor water levels" in result["recommendations"]
    assert "Contact emergency services" in result["recommendations"]
    assert result["model_version"] == risk_engine.MODEL_VERSION


def test_safe_location_low_risk():
    result = assess_risk(SAFE)
    assert result["risk_level"] == "LOW"
    assert result["probability"] < 0.33


def test_factors_sorted_by_contribution():
    result = assess_risk(DADU_LIKE)
    factors = result["main_factors"]
    contribs = result["contributions"]
    labels = {v: k for k, v in risk_engine.FACTOR_LABELS.items()}
    order = [contribs[labels[f]] for f in factors]
    assert order == sorted(order, reverse=True)


def test_medium_recommendations():
    mid = dict(SAFE)
    mid["rainfall_mm"] = 90.0
    mid["river_distance_km"] = 3.0
    mid["elevation_m"] = 150.0
    mid["humidity_pct"] = 80.0
    result = assess_risk(mid)
    assert result["risk_level"] == "MEDIUM"
    assert "Monitor weather forecasts and river levels" in result["recommendations"]
