"""Latest weather observations per district for the command center.

Read from the weather_observations table populated by the early-warning
ingestion pipeline. Authority-only.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import GeographicData, User, WeatherObservation, ROLE_AUTHORITY
from app.schemas import WeatherLatestOut

router = APIRouter()

authority_only = require_role(ROLE_AUTHORITY)


@router.get("/latest", response_model=list[WeatherLatestOut])
def latest_weather(
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Most recent observation for every district that has any."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    latest = (
        db.query(
            WeatherObservation.geographic_id,
            func.max(WeatherObservation.observed_at).label("latest"),
        )
        .group_by(WeatherObservation.geographic_id)
        .subquery()
    )
    rows = (
        db.query(WeatherObservation, GeographicData.district_name)
        .join(latest, (WeatherObservation.geographic_id == latest.c.geographic_id)
              & (WeatherObservation.observed_at == latest.c.latest))
        .join(GeographicData, WeatherObservation.geographic_id == GeographicData.id)
        .order_by(GeographicData.district_name)
        .all()
    )
    return [
        WeatherLatestOut(
            district_name=dname,
            observed_at=obs.observed_at,
            rainfall_mm=obs.rainfall_mm,
            temperature_c=obs.temperature_c,
            humidity_pct=obs.humidity_pct,
            source=obs.source,
        )
        for obs, dname in rows
    ]
