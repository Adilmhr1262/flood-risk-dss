"""Decision support API for disaster management authorities.

Combines predictions, alerts, vulnerability indicators, shelters,
infrastructure and resource allocations into operational views:

- GET /decision-support/summary  — risk overview, explanations, resources
- GET /decision-support/trends   — year-wise and seasonal flood analysis
- GET /decision-support/resources — resource allocations (authority sees all)
- POST /decision-support/resources — record an allocation (authority only)
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.gis import _latest_predictions_subquery, _priority_class
from app.core.deps import get_db, require_role
from app.models import (
    Alert,
    FloodEvent,
    GeographicData,
    Infrastructure,
    Prediction,
    ResourceAllocation,
    Shelter,
    User,
    VulnerabilityIndicator,
    ROLE_AUTHORITY,
    ROLE_NGO,
    ROLE_PUBLIC,
)
from app.schemas import ResourceAllocationCreate, ResourceAllocationOut

router = APIRouter()
staff_only = require_role(ROLE_AUTHORITY, ROLE_NGO)
authority_only = require_role(ROLE_AUTHORITY)
all_roles = require_role(ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC)


def _require_db(db):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")


def _explain_prediction(prediction: Prediction) -> list[dict[str, Any]]:
    """Top contributing features for a stored prediction.

    Recomputes per-feature contributions with the registered model's
    explainability method when the model is available; otherwise falls back
    to the stored main factor labels.
    """
    stored = list(prediction.main_factors or [])
    features = dict(prediction.input_features or {})
    features.pop("district_name", None)
    try:
        from ml.predict import FloodPredictor  # local import: keeps app import light
        from pathlib import Path

        from app.services.prediction_service import PredictionService

        registry = PredictionService(db=None).registry
        entry = registry.get(prediction.model_version) or {}
        for _name, meta in registry.items():
            if meta.get("version") == prediction.model_version and meta.get("type") == "sklearn":
                model_dir = Path(__file__).resolve().parents[3] / meta["model_dir"]
                if (model_dir / "model.joblib").exists():
                    return FloodPredictor.load(model_dir).explain(features)[:5]
                break
        _ = entry
    except Exception:
        pass
    return [{"feature": f, "contribution": None} for f in stored[:5]]




@router.get("/summary")
def summary(db: Session | None = Depends(get_db), user: User = Depends(staff_only)):
    """Operational decision support summary for authorities and NGOs."""
    _require_db(db)

    body = build_situation_summary(db)
    if user.role == ROLE_AUTHORITY:
        body["allocations"] = [
            {
                "id": str(r.id),
                "district_name": g.district_name if g else None,
                "resource_type": r.resource_type,
                "quantity": r.quantity,
                "status": r.status,
                "allocated_at": r.allocated_at.isoformat() if r.allocated_at else None,
                "notes": r.notes,
            }
            for r, g in db.query(ResourceAllocation, GeographicData)
            .outerjoin(GeographicData, ResourceAllocation.geographic_id == GeographicData.id)
            .order_by(ResourceAllocation.allocated_at.desc())
            .all()
        ]
    return body


def build_situation_summary(db: Session) -> dict[str, Any]:
    """Public-safety situation overview.

    Shared by the authenticated ``/decision-support/summary`` endpoint and
    the unauthenticated ``/public/situation`` endpoint that powers the
    FloodSafe Pakistan public website. Contains no role-restricted data.
    """

    sub = _latest_predictions_subquery(db)
    latest = (
        db.query(Prediction, GeographicData)
        .join(GeographicData, Prediction.geographic_id == GeographicData.id)
        .join(sub, (Prediction.geographic_id == sub.c.geographic_id) & (Prediction.predicted_at == sub.c.latest))
        .order_by(Prediction.probability.desc())
        .all()
    )

    high_risk_districts = []
    latest_predictions = []
    for p, g in latest:
        latest_predictions.append(
            {
                "district_name": g.district_name,
                "province": g.province,
                "probability": round(p.probability, 4),
                "risk_level": p.risk_level,
                "model_version": p.model_version,
                "predicted_at": p.predicted_at.isoformat() if p.predicted_at else None,
            }
        )
        if p.risk_level == "HIGH":
            high_risk_districts.append(
                {
                    "district_name": g.district_name,
                    "province": g.province,
                    "probability": round(p.probability, 4),
                    "risk_level": p.risk_level,
                    "model_version": p.model_version,
                    "predicted_at": p.predicted_at.isoformat() if p.predicted_at else None,
                    "top_factors": _explain_prediction(p),
                    "recommended_actions": list(p.recommendations or []),
                }
            )

    alerts = (
        db.query(Alert, GeographicData)
        .join(GeographicData, Alert.geographic_id == GeographicData.id)
        .filter(Alert.is_active.is_(True))
        .order_by(Alert.issued_at.desc())
        .all()
    )
    active_alerts = [
        {
            "id": str(a.id),
            "title": a.title,
            "message": a.message,
            "severity": a.severity,
            "district_name": g.district_name,
            "issued_at": a.issued_at.isoformat() if a.issued_at else None,
        }
        for a, g in alerts
    ]

    shelter_rows = db.query(Shelter).all()
    shelter_capacity = sum(s.capacity or 0 for s in shelter_rows)
    infra_counts = dict(
        db.query(Infrastructure.type, func.count(Infrastructure.id)).group_by(Infrastructure.type).all()
    )
    alloc_status = dict(
        db.query(ResourceAllocation.status, func.count(ResourceAllocation.id))
        .group_by(ResourceAllocation.status)
        .all()
    )
    resource_overview = {
        "shelters": {"count": len(shelter_rows), "total_capacity": shelter_capacity},
        "infrastructure_by_type": infra_counts,
        "allocations_by_status": alloc_status,
        "sample_data_warning": any(
            db.query(Infrastructure.is_sample_data).filter(Infrastructure.is_sample_data.is_(True)).limit(1).all()
        ),
    }

    vuln_rows = (
        db.query(VulnerabilityIndicator, GeographicData, Prediction)
        .join(GeographicData, VulnerabilityIndicator.geographic_id == GeographicData.id)
        .outerjoin(sub, GeographicData.id == sub.c.geographic_id)
        .outerjoin(
            Prediction,
            (Prediction.geographic_id == sub.c.geographic_id) & (Prediction.predicted_at == sub.c.latest),
        )
        .all()
    )
    hotspots = []
    for v, g, p in vuln_rows:
        priority = _priority_class(p.risk_level if p else None, v.vulnerability_index)
        if priority in ("CRITICAL", "HIGH"):
            hotspots.append(
                {
                    "district_name": g.district_name,
                    "province": g.province,
                    "vulnerability_index": round(v.vulnerability_index, 4),
                    "population_density": v.population_density,
                    "risk_level": p.risk_level if p else None,
                    "priority": priority,
                }
            )
    hotspots.sort(key=lambda h: (h["priority"] != "CRITICAL", -(h["vulnerability_index"] or 0)))

    body: dict[str, Any] = {
        "high_risk_districts": high_risk_districts,
        "active_alerts": active_alerts,
        "latest_predictions": latest_predictions,
        "resource_overview": resource_overview,
        "vulnerability_hotspots": hotspots,
    }
    return body


@router.get("/trends")
def trends(db: Session | None = Depends(get_db), _user: User = Depends(staff_only)):
    """Year-wise flood counts per district (2010-2024), seasonal month
    distribution, and a simple trend indicator per district.

    flood_events carries full dates, so month-level seasonality is computed
    directly; districts with no events report zero counts.
    """
    _require_db(db)

    year_rows = (
        db.query(
            GeographicData.district_name,
            func.extract("year", FloodEvent.event_date).label("year"),
            func.count(FloodEvent.id).label("events"),
            func.avg(FloodEvent.severity).label("avg_severity"),
        )
        .join(GeographicData, FloodEvent.geographic_id == GeographicData.id)
        .group_by(GeographicData.district_name, func.extract("year", FloodEvent.event_date))
        .order_by(GeographicData.district_name, "year")
        .all()
    )
    by_district: dict[str, dict] = {}
    for district, year, events, avg_sev in year_rows:
        d = by_district.setdefault(district, {"district_name": district, "years": {}})
        d["years"][int(year)] = {"events": events, "avg_severity": round(float(avg_sev), 2) if avg_sev else None}

    year_wise = []
    for district, d in sorted(by_district.items()):
        years = d["years"]
        # Simple trend: compare mean events in 2010-2016 vs 2017-2024.
        early = [years[y]["events"] for y in years if y <= 2016]
        late = [years[y]["events"] for y in years if y >= 2017]
        trend = "stable"
        if early and late:
            e_mean, l_mean = sum(early) / len(early), sum(late) / len(late)
            if l_mean > e_mean * 1.25:
                trend = "increasing"
            elif l_mean < e_mean * 0.75:
                trend = "decreasing"
        year_wise.append(
            {
                "district_name": district,
                "yearly": [{"year": y, **years[y]} for y in sorted(years)],
                "total_events": sum(v["events"] for v in years.values()),
                "trend_2017_2024_vs_2010_2016": trend,
            }
        )

    month_rows = (
        db.query(
            func.extract("month", FloodEvent.event_date).label("month"),
            func.count(FloodEvent.id).label("events"),
        )
        .group_by(func.extract("month", FloodEvent.event_date))
        .order_by("month")
        .all()
    )
    seasonal = [{"month": int(m), "events": e} for m, e in month_rows]

    return {
        "year_wise": year_wise,
        "seasonal_pattern": seasonal,
        "note": "Counts reflect documented flood events in the database; "
                "under-reporting of minor events is a known limitation.",
    }


@router.get("/resources", response_model=list[ResourceAllocationOut])
def list_resources(db: Session | None = Depends(get_db), _user: User = Depends(staff_only)):
    """Resource allocations with district names (authority/NGO)."""
    _require_db(db)
    rows = (
        db.query(ResourceAllocation, GeographicData)
        .outerjoin(GeographicData, ResourceAllocation.geographic_id == GeographicData.id)
        .order_by(ResourceAllocation.allocated_at.desc())
        .all()
    )
    return [
        ResourceAllocationOut(
            id=r.id,
            district_name=g.district_name if g else None,
            resource_type=r.resource_type,
            quantity=r.quantity,
            status=r.status,
            allocated_at=r.allocated_at,
            notes=r.notes,
        )
        for r, g in rows
    ]


@router.post("/resources", response_model=ResourceAllocationOut, status_code=status.HTTP_201_CREATED)
def create_resource(
    payload: ResourceAllocationCreate,
    db: Session | None = Depends(get_db),
    user: User = Depends(authority_only),
):
    """Record a resource allocation (authority only)."""
    _require_db(db)
    geo = (
        db.query(GeographicData)
        .filter(GeographicData.district_name.ilike(payload.district_name.strip()))
        .first()
    )
    if geo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="District not found")
    row = ResourceAllocation(
        geographic_id=geo.id,
        resource_type=payload.resource_type,
        quantity=payload.quantity,
        allocated_by=user.id,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ResourceAllocationOut(
        id=row.id,
        district_name=geo.district_name,
        resource_type=row.resource_type,
        quantity=row.quantity,
        status=row.status,
        allocated_at=row.allocated_at,
        notes=row.notes,
    )


# Keep the linter quiet about the intentionally unused import.
_ = ROLE_PUBLIC
