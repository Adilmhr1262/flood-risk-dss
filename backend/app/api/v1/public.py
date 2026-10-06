"""Unauthenticated public-safety endpoints for the FloodSafe Pakistan website.

These read-only endpoints expose the same public-safety information that the
authenticated API serves (risk zones, alerts, shelters, emergency contacts),
without requiring a login — ordinary citizens must be able to check flood
risk and find help during an emergency without an account.

No write operations and no role-restricted data (resource allocations,
user management) are exposed here. Each endpoint reuses the same query
logic as its authenticated counterpart so the public website can never
drift from the authoritative data.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1 import gis as gis_endpoints
from app.api.v1.decision_support import build_situation_summary
from app.core.deps import get_db
from app.models import GeographicData
from app.schemas.risk import RiskAssessmentInput
from app.services.alert_engine import _district_history, _district_weather_features
from app.services.prediction_service import DEFAULT_MODEL, PredictionService

router = APIRouter()


def _require_db(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )
    return db


@router.get("/situation")
def situation(db: Session | None = Depends(get_db)):
    """Live flood situation: high-risk districts, active alerts, latest risk updates."""
    db = _require_db(db)
    body = build_situation_summary(db)
    body["generated_at"] = datetime.now(timezone.utc).isoformat()
    return body


@router.get("/risk-check")
def risk_check(
    district_name: str = Query(min_length=2, max_length=150),
    model: str = Query(default=DEFAULT_MODEL),
    db: Session | None = Depends(get_db),
):
    """No-login risk check for one district.

    Assembles the prediction inputs from stored district attributes, the
    latest weather observations/forecast, and flood history — the same
    pipeline the automated early-warning cycle uses — then runs the
    prediction without persisting it (anonymous checks are not stored).
    """
    db = _require_db(db)
    district = (
        db.query(GeographicData)
        .filter(GeographicData.district_name.ilike(district_name.strip()))
        .first()
    )
    if district is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_name}' is not covered by this service",
        )
    weather = _district_weather_features(db, district)
    history = _district_history(db, district)
    inputs = RiskAssessmentInput(
        district_name=district.district_name,
        rainfall_mm=weather["rainfall_mm"],
        temperature_c=weather["temperature_c"],
        humidity_pct=weather["humidity_pct"],
        elevation_m=district.elevation_m or 0.0,
        river_distance_km=district.river_distance_km or 0.0,
        slope_deg=district.slope_deg or 0.0,
        population_density=district.population_density_per_km2 or 0.0,
        prev_flood_events=history["prev_flood_events"],
        last_severity=history["last_severity"],
        vulnerability_index=district.vulnerability_index,
    )
    # db=None: run the assessment without persisting the anonymous check.
    service = PredictionService(db=None)
    result = service.assess(district.district_name, inputs, model_name=model)
    return {
        "district_name": district.district_name,
        "province": district.province,
        "probability": result["probability"],
        "risk_level": result["risk_level"],
        "model_version": result["model_version"],
        "main_factors": list(result["main_factors"] or []),
        "recommendations": list(result["recommendations"] or []),
        "feature_contributions": result.get("feature_contributions") or [],
        "inputs_used": {
            "rainfall_mm": inputs.rainfall_mm,
            "temperature_c": inputs.temperature_c,
            "humidity_pct": inputs.humidity_pct,
            "prev_flood_events": inputs.prev_flood_events,
            "last_severity": inputs.last_severity,
        },
        "note": result.get("note"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/map/risk-zones")
def map_risk_zones(db: Session | None = Depends(get_db)):
    """Per-district flood risk zones as GeoJSON (same data as /gis/risk-layer)."""
    db = _require_db(db)
    return gis_endpoints.risk_layer(db=db, _user=None)


@router.get("/map/resources")
def map_resources(
    type: str | None = Query(default=None, description="shelter|hospital|rescue_center|emergency_facility"),
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
):
    """Shelters, hospitals, rescue centres and emergency facilities as GeoJSON.

    Shelters are served from the dedicated shelter registry (same data as
    the authenticated /gis/shelters layer); all other types come from the
    infrastructure layer.
    """
    db = _require_db(db)
    if type == "shelter":
        collection = gis_endpoints.shelter_layer(db=db, _user=None)
        if district_name:
            needle = district_name.strip().lower()
            collection.features = [
                f
                for f in collection.features
                if needle in (f.properties.get("district_name") or "").lower()
            ]
        return collection
    return gis_endpoints.infrastructure_layer(type=type, district_name=district_name, db=db, _user=None)


@router.get("/emergency-contacts")
def emergency_contacts(
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
):
    """Emergency rescue / relief contact directory, optionally filtered by district."""
    db = _require_db(db)
    return gis_endpoints.emergency_contact_layer(district_name=district_name, db=db, _user=None)


@router.get("/districts")
def districts(db: Session | None = Depends(get_db)):
    """Districts covered by the service, for dropdowns and search."""
    db = _require_db(db)
    rows = (
        db.query(GeographicData.district_name, GeographicData.province)
        .order_by(GeographicData.district_name)
        .all()
    )
    return {
        "districts": [{"district_name": name, "province": province} for name, province in rows],
        "count": len(rows),
    }


@router.get("/historical-floods")
def historical_floods(
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
):
    """Historical flood events as GeoJSON (same data as /gis/historical-floods)."""
    db = _require_db(db)
    return gis_endpoints.historical_floods(district_name=district_name, db=db, _user=None)
