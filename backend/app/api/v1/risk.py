"""Risk assessment endpoints: run predictions and read prediction history."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import GeographicData, Prediction, User, ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC
from app.schemas import PredictionOut, RiskAssessmentInput, RiskAssessmentOutput
from app.schemas.common import PaginatedResponse, Pagination
from app.services.prediction_service import (
    BACKEND_DIR,
    DEFAULT_MODEL,
    PredictionService,
    UnknownDistrictError,
)

router = APIRouter()
all_roles = require_role(ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC)


@router.post("/predict", response_model=RiskAssessmentOutput)
def predict(
    payload: RiskAssessmentInput,
    model: str = Query(
        default=DEFAULT_MODEL,
        description="Model from the registry: rf-v1 (default) or rule-based-v1",
    ),
    db: Session | None = Depends(get_db),
    user: User = Depends(all_roles),
):
    service = PredictionService(db)
    try:
        result = service.assess(
            payload.district_name, payload, model_name=model, user_id=user.id
        )
    except UnknownDistrictError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return RiskAssessmentOutput(**result)


@router.get("/predictions", response_model=PaginatedResponse)
def prediction_history(
    pagination: Pagination = Depends(),
    district_name: str | None = None,
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    query = db.query(Prediction).order_by(Prediction.predicted_at.desc())
    if district_name:
        query = (
            query.join(GeographicData, Prediction.geographic_id == GeographicData.id)
            .filter(GeographicData.district_name.ilike(f"%{district_name}%"))
        )
    total = query.count()
    rows = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).all()
    items = [
        PredictionOut(
            id=r.id,
            geographic_id=r.geographic_id,
            probability=r.probability,
            risk_level=r.risk_level,
            main_factors=list(r.main_factors or []),
            recommendations=list(r.recommendations or []),
            model_version=r.model_version,
            predicted_at=r.predicted_at,
        ).model_dump()
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/model-info")
def model_info(_user: User = Depends(all_roles)):
    """Return the model registry with metrics and feature importance."""
    service = PredictionService()
    models = {}
    for name, entry in service.available_models().items():
        enriched = dict(entry)
        if entry.get("type") == "sklearn":
            importance_path = BACKEND_DIR / entry["model_dir"] / "feature_importance.json"
            if importance_path.exists():
                enriched["feature_importance"] = json.loads(importance_path.read_text())
        models[name] = enriched
    return {"models": models, "default_model": DEFAULT_MODEL}
