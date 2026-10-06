"""Prediction service: model registry plus unified risk assessment.

Every assessment runs the deterministic rule-based engine (always
available) and, when requested and available, a registered machine
learning model. The merged result follows the standard assessment
contract and is persisted to the ``predictions`` table.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import GeographicData, Prediction
from app.schemas.risk import RiskAssessmentInput
from app.services.risk_engine import (
    MODEL_VERSION as RULE_BASED_VERSION,
    RECOMMENDATIONS,
    assess_risk,
    risk_level,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
REPO_ROOT = BACKEND_DIR.parent  # repository root
# Model artifacts live at the repository root so training code, the API
# service, and docs all share one location. Override with env vars when the
# checkout layout differs (e.g. container images).
MODEL_DIR = Path(os.environ.get("MODEL_DIR", REPO_ROOT / "ml-models"))
REGISTRY_PATH = Path(os.environ.get("MODEL_REGISTRY_PATH", MODEL_DIR / "registry.json"))
DEFAULT_MODEL = "rf-v1"


class UnknownDistrictError(ValueError):
    """Raised when a district name is not registered in geographic_data."""


class PredictionService:
    """Unified entry point for flood risk assessment.

    Args:
        db: SQLAlchemy session (None disables persistence and district
            validation, keeping the no-DB graceful fallback).
        registry_path: override for ml-models/registry.json (used in tests).
    """

    def __init__(self, db: Session | None = None, registry_path: Path | None = None):
        self.db = db
        path = Path(registry_path) if registry_path else REGISTRY_PATH
        self.registry: dict = json.loads(path.read_text()) if path.exists() else {}

    def available_models(self) -> dict:
        """Return the model registry."""
        return self.registry

    def _resolve_district(self, district_name: str) -> tuple[UUID, str]:
        """Resolve a district name to (geographic_id, canonical name)."""
        row = (
            self.db.query(GeographicData)
            .filter(func.lower(GeographicData.district_name) == district_name.strip().lower())
            .first()
        )
        if row is None:
            raise UnknownDistrictError(
                f"District '{district_name}' is not registered in geographic_data"
            )
        return row.id, row.district_name

    def _ml_result(self, model_name: str, features: dict) -> tuple[float, list[dict]] | None:
        """Return (probability, top feature contributions) for a registered
        ML model, or None when the model is unavailable."""
        entry = self.registry.get(model_name)
        if not entry or entry.get("type") != "sklearn":
            return None
        model_dir = REPO_ROOT / entry["model_dir"]
        if not (model_dir / "model.joblib").exists():
            return None
        from ml.predict import FloodPredictor  # local import: keeps app import light

        predictor = FloodPredictor.load(model_dir)
        return predictor.predict_proba(features), predictor.explain(features)

    def assess(
        self,
        district_name: str,
        inputs: RiskAssessmentInput,
        model_name: str = DEFAULT_MODEL,
        user_id: UUID | None = None,
    ) -> dict:
        """Run a risk assessment and persist it.

        Always runs the rule-based engine for transparent risk factors;
        uses the requested ML model's probability when available, otherwise
        falls back to the rule-based score with an explanatory note.

        Returns:
            dict matching RiskAssessmentOutput plus model_requested/note.
        """
        base_features = inputs.model_dump(exclude={"district_name"})
        rule = assess_risk(base_features)

        ml_result = self._ml_result(model_name, base_features)
        note = None
        feature_contributions: list[dict] = []
        if ml_result is not None:
            ml_proba, feature_contributions = ml_result
            probability = round(ml_proba, 4)
            level = risk_level(probability)
            model_version = self.registry[model_name]["version"]
            main_factors = rule["main_factors"]
            recommendations = list(RECOMMENDATIONS[level])
        else:
            probability = rule["probability"]
            level = rule["risk_level"]
            model_version = RULE_BASED_VERSION
            main_factors = rule["main_factors"]
            recommendations = rule["recommendations"]
            if model_name != "rule-based-v1":
                note = (
                    f"Requested model '{model_name}' is unavailable; "
                    "fell back to the rule-based v1 engine."
                )

        prediction_id = None
        canonical_name = district_name
        geographic_id = None
        if self.db is not None:
            geographic_id, canonical_name = self._resolve_district(district_name)
        # Stored feature vector keeps the district name inline so each
        # persisted assessment is self-describing for audit and retraining.
        stored_features = {**base_features, "district_name": canonical_name}
        if self.db is not None:
            row = Prediction(
                geographic_id=geographic_id,
                model_version=model_version,
                probability=probability,
                risk_level=level,
                input_features=stored_features,
                main_factors=main_factors,
                recommendations=recommendations,
                created_by=user_id,
            )
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            prediction_id = row.id

        return {
            "district_name": canonical_name,
            "probability": probability,
            "risk_level": level,
            "main_factors": main_factors,
            "recommendations": recommendations,
            "model_version": model_version,
            "prediction_id": prediction_id,
            "model_requested": model_name,
            "note": note,
            "feature_contributions": feature_contributions,
        }
