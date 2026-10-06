"""Thin orchestration layer over the modular machine learning pipeline.

Keeps the historical ``ml.pipeline`` import surface (load_dataset, clean,
engineer_features, train_models, evaluate, save_model, load_model) while
delegating each stage to its focused module. New code should import the
stage modules directly.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml import data_loader, evaluate as evaluate_module, feature_engineering, preprocessing
from ml.data_loader import BASE_FEATURES

REPO_ROOT = Path(__file__).resolve().parents[2]  # repository root
DEFAULT_OUT_DIR = REPO_ROOT / "ml-models" / "models" / "rf-v1"

RANDOM_STATE = 42

# Phase 3 research models train on the nine base features plus the documented
# vulnerability composite (see data/processed/DATA_CARD.md).
RESEARCH_FEATURES = BASE_FEATURES + ["vulnerability_index"]

# Backwards-compatible aliases for the original pipeline surface.
load_dataset = data_loader.load_training_data
clean = preprocessing.clean
save_model = joblib.dump
load_model = joblib.load
evaluate = evaluate_module.evaluate


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy helper: return the frame with engineered features added."""
    df = df.copy()
    X, _, names = feature_engineering.engineer(df)
    for name in names:
        if name not in df.columns:
            df[name] = X[name]
    return df


def build_classifier(name: str):
    """Instantiate a classifier by short name: rf | xgb | mlp."""
    if name == "rf":
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_split=2,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
    if name == "mlp":
        # Multi-layer perceptron variant.
        return MLPClassifier(
            hidden_layer_sizes=(64, 32), max_iter=800, random_state=RANDOM_STATE
        )
    if name == "xgb":
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=RANDOM_STATE,
            eval_metric="logloss",
            n_jobs=-1,
        )
    raise ValueError(f"Unknown model '{name}'. Choose rf, xgb, or mlp.")


def train_models(df: pd.DataFrame, models: tuple[str, ...] = ("rf",)):
    """Legacy helper: train sklearn pipelines on an already-loaded frame."""
    df = preprocessing.clean(df)
    X, y, _ = feature_engineering.engineer(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    trained = {}
    for name in models:
        pipe = Pipeline([("scaler", StandardScaler()), ("classifier", build_classifier(name))])
        pipe.fit(X_train, y_train)
        trained[name] = pipe
    return trained, (X_train, X_test, y_train, y_test)


def feature_importance(model, feature_names: list[str]) -> dict[str, float] | None:
    """Extract per-feature importance from tree-based models (None otherwise)."""
    clf = model.named_steps.get("classifier", model) if hasattr(model, "named_steps") else model
    importances = getattr(clf, "feature_importances_", None)
    if importances is None:
        return None
    total = float(np.sum(importances)) or 1.0
    return {
        name: round(float(v) / total, 4)
        for name, v in sorted(
            zip(feature_names, importances), key=lambda kv: kv[1], reverse=True
        )
    }


def permutation_feature_importance(
    model, X: pd.DataFrame, y: pd.Series, feature_names: list[str]
) -> dict[str, float]:
    """Model-agnostic importance via permutation (used for the MLP).

    Shuffles each feature (10 repeats, fixed seed) and measures the mean
    drop in F1 on the given set; importances are normalised to sum to 1.
    """
    result = permutation_importance(
        model, X, y, n_repeats=10, random_state=RANDOM_STATE, scoring="f1", n_jobs=-1
    )
    raw = np.clip(result.importances_mean, 0.0, None)
    total = float(np.sum(raw)) or 1.0
    return {
        name: round(float(v) / total, 4)
        for name, v in sorted(
            zip(feature_names, raw), key=lambda kv: kv[1], reverse=True
        )
    }


def dataset_version_info(source: str) -> dict:
    """Provenance record for the training data: sha256, rows, date range."""
    info: dict = {"source": source}
    p = Path(source)
    if p.is_file():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        info["sha256"] = h.hexdigest()
        try:
            df = pd.read_csv(p, usecols=["year"])
            info["n_rows"] = int(len(df))
            info["year_min"] = int(df["year"].min())
            info["year_max"] = int(df["year"].max())
        except Exception:
            pass
    return info


def run_training(
    source: str = "db",
    model_name: str = "rf",
    out_dir: str | Path = DEFAULT_OUT_DIR,
    database_url: str | None = None,
    feature_columns: list[str] | None = None,
) -> dict:
    """Full training run: load -> clean -> engineer -> split -> CV -> train
    -> evaluate -> persist.

    Args:
        feature_columns: base feature columns to train on; defaults to the
            nine ``BASE_FEATURES``. Phase 3 research models pass
            ``RESEARCH_FEATURES`` (ten, adding ``vulnerability_index``).

    Persists into ``out_dir``: model.joblib, feature_names.json,
    preprocessing.json, metrics.json, feature_importance.json,
    feature_stats.json (per-feature mean/std for explainability).

    Returns:
        dict with model_dir, metrics, feature_importance, n_rows, cv scores.
    """
    df = data_loader.load_training_data(source, database_url=database_url)
    features = list(feature_columns) if feature_columns else list(BASE_FEATURES)
    issues = preprocessing.validate_ranges(df, features)
    df = preprocessing.clean(df, features)
    prep_params = preprocessing.fit_preprocessing(df, features)
    X, y, feature_names = feature_engineering.engineer(df, features)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    pipe = Pipeline(
        [("scaler", StandardScaler()), ("classifier", build_classifier(model_name))]
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1")
    pipe.fit(X_train, y_train)

    metrics = evaluate_module.evaluate(pipe, X_test, y_test)
    metrics["cv_f1_mean"] = round(float(np.mean(cv_scores)), 4)
    metrics["cv_f1_std"] = round(float(np.std(cv_scores)), 4)
    importance = feature_importance(pipe, feature_names)
    importance_method = "built-in"
    if importance is None:
        # e.g. the MLP has no native importances: fall back to permutation
        # importance measured on the held-out test set.
        importance = permutation_feature_importance(pipe, X_test, y_test, feature_names)
        importance_method = "permutation"
    stats = {
        name: {"mean": round(float(X[name].mean()), 6), "std": round(float(X[name].std()) or 1.0, 6)}
        for name in feature_names
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out / "model.joblib")
    (out / "feature_names.json").write_text(json.dumps(feature_names, indent=2))
    (out / "preprocessing.json").write_text(json.dumps(prep_params, indent=2))
    (out / "feature_stats.json").write_text(json.dumps(stats, indent=2))
    metrics_payload = {
        **metrics,
        "model": model_name,
        "feature_columns": features,
        "importance_method": importance_method,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(df),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "data_source": source,
        "dataset": dataset_version_info(source),
        "range_issues": issues,
    }
    (out / "metrics.json").write_text(json.dumps(metrics_payload, indent=2))
    (out / "feature_importance.json").write_text(
        json.dumps(importance if importance is not None else {}, indent=2)
    )
    return {
        "model_dir": str(out),
        "metrics": metrics_payload,
        "feature_importance": importance,
        "n_rows": len(df),
    }
