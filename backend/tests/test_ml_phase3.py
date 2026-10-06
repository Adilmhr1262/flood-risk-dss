"""Phase 3 tests: research models (randomforest/xgboost/mlp), registry
aliases, contribution-based explanations, and legacy compatibility."""

import json
from pathlib import Path

import pytest

from ml.data_loader import BASE_FEATURES
from ml.pipeline import RESEARCH_FEATURES
from ml.predict import FloodPredictor

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
MODELS_DIR = REPO_ROOT / "ml-models" / "models"
REGISTRY = json.loads((REPO_ROOT / "ml-models" / "registry.json").read_text())

PHASE3_MODELS = ["randomforest-v1", "xgboost-v1", "mlp-v1"]
ALIASES = {"randomforest": "randomforest-v1", "xgboost": "xgboost-v1", "mlp": "mlp-v1"}

ARTIFACTS = (
    "model.joblib",
    "feature_names.json",
    "preprocessing.json",
    "feature_stats.json",
    "metrics.json",
    "feature_importance.json",
    "confusion_matrix.png",
)

TEN_FEATURES = {
    "rainfall_mm": 650.0,
    "temperature_c": 33.0,
    "humidity_pct": 72.0,
    "elevation_m": 62.0,
    "river_distance_km": 14.0,
    "slope_deg": 1.2,
    "population_density": 268.0,
    "prev_flood_events": 3,
    "last_severity": 4,
    "vulnerability_index": 0.33,
}


def test_research_features_are_ten():
    assert RESEARCH_FEATURES == BASE_FEATURES + ["vulnerability_index"]
    assert len(RESEARCH_FEATURES) == 10


@pytest.mark.parametrize("name", PHASE3_MODELS)
def test_model_artifacts_exist(name):
    d = MODELS_DIR / name
    for fname in ARTIFACTS:
        assert (d / fname).exists(), f"{name}/{fname}"
    # confusion matrix PNG must be a real image, not empty
    assert (d / "confusion_matrix.png").stat().st_size > 1000


@pytest.mark.parametrize("name", PHASE3_MODELS)
def test_model_feature_names_are_fourteen(name):
    names = json.loads((MODELS_DIR / name / "feature_names.json").read_text())
    assert len(names) == 14  # 10 base + 4 engineered
    for col in RESEARCH_FEATURES:
        assert col in names


@pytest.mark.parametrize("name", PHASE3_MODELS)
def test_model_metrics_and_provenance(name):
    metrics = json.loads((MODELS_DIR / name / "metrics.json").read_text())
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc",
                "cv_f1_mean", "cv_f1_std"):
        assert 0.0 <= metrics[key] <= 1.0, key
    assert metrics["n_rows"] == 180
    assert metrics["dataset"]["n_rows"] == 180
    assert metrics["dataset"]["year_min"] == 2010
    assert metrics["dataset"]["year_max"] == 2024
    assert len(metrics["dataset"]["sha256"]) == 64
    assert metrics["feature_columns"] == RESEARCH_FEATURES


@pytest.mark.parametrize("name", PHASE3_MODELS)
def test_feature_importance_normalised(name):
    importance = json.loads((MODELS_DIR / name / "feature_importance.json").read_text())
    assert len(importance) == 14
    assert sum(importance.values()) == pytest.approx(1.0, abs=1e-3)


def test_registry_entries_and_aliases():
    for name in PHASE3_MODELS:
        assert name in REGISTRY, name
        assert REGISTRY[name]["type"] == "sklearn"
        assert (REPO_ROOT / REGISTRY[name]["model_dir"] / "model.joblib").exists()
    for alias, canonical in ALIASES.items():
        assert alias in REGISTRY, alias
        assert REGISTRY[alias]["model_dir"] == REGISTRY[canonical]["model_dir"]
        assert REGISTRY[alias]["version"] == canonical
    # legacy models untouched
    assert "rf-v1" in REGISTRY
    assert "rule-based-v1" in REGISTRY


@pytest.mark.parametrize("name", PHASE3_MODELS)
def test_predict_and_explain(name):
    predictor = FloodPredictor.load(MODELS_DIR / name)
    proba = predictor.predict_proba(TEN_FEATURES)
    assert 0.0 <= proba <= 1.0
    explanation = predictor.explain(TEN_FEATURES)
    assert len(explanation) == 5
    for row in explanation:
        assert set(row) == {"feature", "contribution", "value"}
        assert row["feature"] in predictor.feature_names
    total = sum(r["contribution"] for r in explanation)
    assert total == pytest.approx(1.0, abs=1e-3)
    # contributions are ordered, highest first
    contribs = [r["contribution"] for r in explanation]
    assert contribs == sorted(contribs, reverse=True)


def test_explain_without_vulnerability_uses_median():
    """vulnerability_index is optional: None must not crash prediction."""
    predictor = FloodPredictor.load(MODELS_DIR / "xgboost-v1")
    feats = {**TEN_FEATURES, "vulnerability_index": None}
    assert 0.0 <= predictor.predict_proba(feats) <= 1.0
    assert len(predictor.explain(feats)) == 5


def test_legacy_rf_v1_unchanged():
    """The Phase 2 model keeps its 9-feature contract and still scores."""
    predictor = FloodPredictor.load(MODELS_DIR / "rf-v1")
    assert len(predictor.feature_names) == 13
    nine = {k: v for k, v in TEN_FEATURES.items() if k in BASE_FEATURES}
    assert 0.0 <= predictor.predict_proba(nine) <= 1.0
    # extra key (vulnerability_index) must not break the legacy model either
    assert 0.0 <= predictor.predict_proba(TEN_FEATURES) <= 1.0
