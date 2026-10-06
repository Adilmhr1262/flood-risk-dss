"""Single-row inference for trained flood risk models.

FloodPredictor loads a trained model directory (produced by ``ml.train``)
and exposes ``predict_proba`` for the nine base input features, applying the
exact preprocessing and feature engineering used during training.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from ml.feature_engineering import ENGINEERED_FEATURES, engineer_row
from ml.preprocessing import apply_preprocessing


class FloodPredictor:
    """Load a trained model directory and score single feature dicts."""

    def __init__(self, model_dir: str | Path):
        self.model_dir = Path(model_dir)
        self.model = joblib.load(self.model_dir / "model.joblib")
        with open(self.model_dir / "feature_names.json") as f:
            self.feature_names: list[str] = json.load(f)
        # Base features are the model's features minus the engineered ones;
        # this keeps old 9-feature models and new 10-feature models working.
        self.base_features: list[str] = [
            f for f in self.feature_names if f not in ENGINEERED_FEATURES
        ]
        with open(self.model_dir / "preprocessing.json") as f:
            self.preprocessing_params: dict = json.load(f)
        with open(self.model_dir / "metrics.json") as f:
            self.metrics: dict = json.load(f)
        stats_path = self.model_dir / "feature_stats.json"
        self.feature_stats: dict = (
            json.loads(stats_path.read_text()) if stats_path.exists() else {}
        )
        imp_path = self.model_dir / "feature_importance.json"
        self.feature_importance: dict = (
            json.loads(imp_path.read_text()) if imp_path.exists() else {}
        )

    @classmethod
    def load(cls, model_dir: str | Path) -> "FloodPredictor":
        return cls(model_dir)

    def predict_proba(self, feature_dict: dict) -> float:
        """Return P(flood) for the model's base input features.

        Args:
            feature_dict: mapping of the model's base feature names to raw
                values (e.g. from ``RiskAssessmentInput``).

        Returns:
            Flood probability in [0, 1].
        """
        cleaned = apply_preprocessing(
            feature_dict, self.preprocessing_params, self.base_features
        )
        engineered = engineer_row(cleaned)
        row = pd.DataFrame([{k: engineered[k] for k in self.feature_names}])
        proba = self.model.predict_proba(row[self.feature_names])
        classes = list(self.model.classes_)
        if 1 in classes:
            return float(proba[0][classes.index(1)])
        return 0.0  # model trained on a single class

    def explain(self, feature_dict: dict, top_n: int = 5) -> list[dict]:
        """Per-feature contribution scores for one prediction.

        Method (documented for research transparency): for each model
        feature, contribution = normalised feature importance x absolute
        z-score of the (preprocessed, engineered) input value against the
        training distribution, re-normalised to sum to 1. It answers "which
        features pushed *this* prediction away from the average?", not a
        causal claim.

        Returns:
            List of {"feature", "contribution", "value"} dicts, top_n first.
        """
        cleaned = apply_preprocessing(
            feature_dict, self.preprocessing_params, self.base_features
        )
        engineered = engineer_row(cleaned)
        scores: dict[str, float] = {}
        for name in self.feature_names:
            imp = float(self.feature_importance.get(name, 0.0))
            stat = self.feature_stats.get(name, {})
            mean = float(stat.get("mean", 0.0))
            std = float(stat.get("std", 1.0)) or 1.0
            z = abs((float(engineered[name]) - mean) / std)
            scores[name] = imp * z
        total = sum(scores.values()) or 1.0
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        shown_total = sum(score for _, score in ranked) or 1.0
        return [
            {
                "feature": name,
                "contribution": round(score / shown_total, 4),
                "value": round(float(engineered[name]), 4),
            }
            for name, score in ranked
        ]
