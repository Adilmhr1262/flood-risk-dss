"""Tests for the modular machine learning pipeline."""

from pathlib import Path

import pandas as pd
import pytest

from ml import data_loader, feature_engineering, preprocessing
from ml.data_loader import BASE_FEATURES
from ml.feature_engineering import MODEL_FEATURES, engineer_row
from ml.pipeline import feature_importance, run_training
from ml.predict import FloodPredictor

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "ml" / "sample_training_data.csv"


def _dirty_frame() -> pd.DataFrame:
    data = {c: [10.0] * 8 for c in BASE_FEATURES}
    data["rainfall_mm"] = [50.0, 60.0, None, 70.0, 80.0, 90.0, 100.0, 100000.0]
    data["flooded"] = [0, 1, 0, 1, 0, 1, 0, 1]
    return pd.DataFrame(data)


def test_clean_imputes_missing_and_caps_outliers():
    cleaned = preprocessing.clean(_dirty_frame())
    assert not cleaned[BASE_FEATURES].isna().any().any()
    # 100000.0 is an extreme outlier: it must be capped below its raw value.
    assert cleaned["rainfall_mm"].max() < 100000.0
    assert set(cleaned["flooded"].unique()) <= {0, 1}


def test_validate_ranges_flags_issues():
    df = _dirty_frame()
    issues = preprocessing.validate_ranges(df)
    assert any("rainfall_mm" in i for i in issues)
    assert isinstance(preprocessing.validate_ranges(preprocessing.clean(df)), list)


def test_engineer_returns_expected_columns():
    df = preprocessing.clean(data_loader.load_sample_csv(SAMPLE_CSV))
    X, y, names = feature_engineering.engineer(df)
    assert names == MODEL_FEATURES
    assert len(names) == 13  # 9 base + 4 engineered
    assert list(X.columns) == MODEL_FEATURES
    assert set(y.unique()) <= {0, 1}
    assert (X["rain_intensity"] >= 0).all()


def test_engineer_row_matches_dataframe_definition():
    row = {c: 100.0 for c in BASE_FEATURES}
    row.update({"humidity_pct": 50.0, "elevation_m": 10.0, "river_distance_km": 2.0,
                "population_density": 500.0, "prev_flood_events": 2.0})
    eng = engineer_row(row)
    assert eng["rain_intensity"] == pytest.approx(50.0)
    assert eng["lowland_river"] == pytest.approx((1 / 11) * (1 / 3))
    assert eng["flood_history_score"] == pytest.approx(2.0)


@pytest.fixture(scope="module")
def trained_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("model")
    result = run_training(source=str(SAMPLE_CSV), model_name="rf", out_dir=out)
    return out, result


def test_run_training_persists_artifacts(trained_dir):
    out, result = trained_dir
    for fname in ("model.joblib", "feature_names.json", "preprocessing.json",
                  "metrics.json", "feature_importance.json"):
        assert (out / fname).exists(), fname
    m = result["metrics"]
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc", "cv_f1_mean"):
        assert 0.0 <= m[key] <= 1.0, key
    assert result["n_rows"] > 0


def test_feature_importance_sums_to_one(trained_dir):
    out, result = trained_dir
    importance = result["feature_importance"]
    assert importance is not None
    assert sum(importance.values()) == pytest.approx(1.0, abs=1e-3)
    assert set(importance) == set(MODEL_FEATURES)


def test_flood_predictor_roundtrip(trained_dir):
    out, _ = trained_dir
    predictor = FloodPredictor.load(out)
    proba = predictor.predict_proba(
        {
            "rainfall_mm": 180.0, "temperature_c": 34.0, "humidity_pct": 92.0,
            "elevation_m": 45.0, "river_distance_km": 1.2, "slope_deg": 1.5,
            "population_density": 950.0, "prev_flood_events": 4, "last_severity": 3,
        }
    )
    assert 0.0 <= proba <= 1.0
    assert set(predictor.feature_names) == set(MODEL_FEATURES)
