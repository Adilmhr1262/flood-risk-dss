"""Tests for the prediction service (registry, model paths, persistence).

Uses the development database; every persisted prediction row created by
these tests is deleted in a finally block.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Prediction
from app.schemas.risk import RiskAssessmentInput
from app.services.prediction_service import (
    PredictionService,
    UnknownDistrictError,
)

DATABASE_URL = (
    "postgresql+psycopg2://flood_dss:flood_dss_dev@localhost:5432/flood_risk_dss"
)

DADU_INPUT = RiskAssessmentInput(
    district_name="Dadu",
    rainfall_mm=180.0,
    temperature_c=34.0,
    humidity_pct=92.0,
    elevation_m=45.0,
    river_distance_km=1.2,
    slope_deg=1.5,
    population_density=950.0,
    prev_flood_events=4,
    last_severity=3,
)


@pytest.fixture(scope="module")
def db():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def service(db):
    return PredictionService(db)


def _delete_prediction(db, prediction_id):
    if prediction_id is not None:
        db.query(Prediction).filter(Prediction.id == prediction_id).delete()
        db.commit()


def test_registry_lists_models(service):
    registry = service.available_models()
    assert "rule-based-v1" in registry
    assert "rf-v1" in registry
    assert registry["rf-v1"]["type"] == "sklearn"
    assert "metrics" in registry["rf-v1"]


def test_ml_model_path_assess_and_persist(service, db):
    result = service.assess("Dadu", DADU_INPUT, model_name="rf-v1")
    try:
        assert result["model_version"] == "rf-v1"
        assert result["model_requested"] == "rf-v1"
        assert result["note"] is None
        assert 0.0 <= result["probability"] <= 1.0
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert result["main_factors"], "rule-based explanations must accompany the ML score"
        assert result["recommendations"]
        assert result["prediction_id"] is not None

        row = db.query(Prediction).filter(Prediction.id == result["prediction_id"]).one()
        assert row.model_version == "rf-v1"
        assert set(row.input_features.keys()) == {
            "district_name",
            "rainfall_mm", "temperature_c", "humidity_pct", "elevation_m",
            "river_distance_km", "slope_deg", "population_density",
            "prev_flood_events", "last_severity", "vulnerability_index",
        }
        assert row.input_features["district_name"] == "Dadu"
        assert list(row.main_factors) == result["main_factors"]
        assert row.geographic_id is not None
    finally:
        _delete_prediction(db, result.get("prediction_id"))


def test_unknown_model_falls_back_to_rule_based(service, db):
    result = service.assess("Dadu", DADU_INPUT, model_name="does-not-exist")
    try:
        assert result["model_version"] == "v1.0.0-rule-based"
        assert result["note"] is not None and "fell back" in result["note"]
        assert result["prediction_id"] is not None
    finally:
        _delete_prediction(db, result.get("prediction_id"))


def test_explicit_rule_based_has_no_note(service, db):
    result = service.assess("Dadu", DADU_INPUT, model_name="rule-based-v1")
    try:
        assert result["model_version"] == "v1.0.0-rule-based"
        assert result["note"] is None
    finally:
        _delete_prediction(db, result.get("prediction_id"))


def test_unknown_district_raises(service):
    bad = DADU_INPUT.model_copy(update={"district_name": "Atlantis"})
    with pytest.raises(UnknownDistrictError):
        service.assess("Atlantis", bad, model_name="rf-v1")


def test_no_db_still_assesses_without_persisting():
    service = PredictionService(db=None)
    result = service.assess("Dadu", DADU_INPUT, model_name="rf-v1")
    assert result["prediction_id"] is None
    assert result["model_version"] == "rf-v1"
    assert 0.0 <= result["probability"] <= 1.0
