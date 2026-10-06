"""Dashboard aggregates: summary cards, rainfall trends, flood frequency, risk distribution."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import Alert, FloodEvent, GeographicData, Prediction, User, ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC, ROLE_VOLUNTEER
from app.schemas import FrequencyPoint, RiskDistribution, SummaryCards, TrendPoint

router = APIRouter()
# Read-only public statistics: visible to every authenticated role.
any_role = require_role(ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC, ROLE_VOLUNTEER)


def _require_db(db):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return db


def _latest(db):
    """One row per geographic_id: the most recent prediction timestamp."""
    return (
        db.query(Prediction.geographic_id, func.max(Prediction.predicted_at).label("latest"))
        .group_by(Prediction.geographic_id)
        .subquery()
    )


def _latest_risk_levels(db):
    """Risk level of the latest prediction per location."""
    sub = _latest(db)
    return (
        db.query(Prediction.risk_level)
        .join(sub, (Prediction.geographic_id == sub.c.geographic_id) & (Prediction.predicted_at == sub.c.latest))
    )


@router.get("/summary", response_model=SummaryCards)
def summary(db: Session | None = Depends(get_db), _user: User = Depends(any_role)):
    _require_db(db)
    active_alerts = db.query(Alert).filter(Alert.is_active.is_(True)).count()
    high_risk_areas = (
        _latest_risk_levels(db)
        .join(GeographicData, GeographicData.id == Prediction.geographic_id)
        .filter(Prediction.risk_level == "HIGH")
        .count()
    )
    total_events = db.query(FloodEvent).count()
    levels = {row[0] for row in _latest_risk_levels(db).all()}
    current = "HIGH" if "HIGH" in levels else ("MEDIUM" if "MEDIUM" in levels else "LOW")
    return SummaryCards(
        active_alerts=active_alerts,
        high_risk_areas=high_risk_areas,
        total_historical_events=total_events,
        current_risk_status=current,
    )


@router.get("/rainfall-trends", response_model=list[TrendPoint])
def rainfall_trends(db: Session | None = Depends(get_db), _user: User = Depends(any_role)):
    """Average recorded rainfall per month (YYYY-MM) across all historical events."""
    _require_db(db)
    rows = (
        db.query(
            func.to_char(FloodEvent.event_date, "YYYY-MM").label("period"),
            func.avg(FloodEvent.rainfall_mm).label("rainfall_mm"),
        )
        .group_by("period")
        .order_by("period")
        .all()
    )
    return [TrendPoint(period=r.period, rainfall_mm=round(float(r.rainfall_mm or 0), 2)) for r in rows]


@router.get("/flood-frequency", response_model=list[FrequencyPoint])
def flood_frequency(db: Session | None = Depends(get_db), _user: User = Depends(any_role)):
    """Number of historical flood events per year."""
    _require_db(db)
    rows = (
        db.query(
            func.to_char(FloodEvent.event_date, "YYYY").label("period"),
            func.count(FloodEvent.id).label("events"),
        )
        .group_by("period")
        .order_by("period")
        .all()
    )
    return [FrequencyPoint(period=r.period, events=int(r.events)) for r in rows]


@router.get("/risk-distribution", response_model=RiskDistribution)
def risk_distribution(db: Session | None = Depends(get_db), _user: User = Depends(any_role)):
    """Count of latest prediction per location grouped by risk level."""
    _require_db(db)
    sub = _latest(db)
    rows = (
        db.query(Prediction.risk_level, func.count(Prediction.geographic_id))
        .join(sub, (Prediction.geographic_id == sub.c.geographic_id) & (Prediction.predicted_at == sub.c.latest))
        .group_by(Prediction.risk_level)
        .all()
    )
    counts = {level: 0 for level in ("LOW", "MEDIUM", "HIGH")}
    for level, count in rows:
        counts[level] = int(count)
    return RiskDistribution(low=counts["LOW"], medium=counts["MEDIUM"], high=counts["HIGH"])
