"""Report generation and data export (authority only)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import FloodEvent, GeographicData, Prediction, User, ROLE_AUTHORITY

import csv
import io

router = APIRouter()
authority_only = require_role(ROLE_AUTHORITY)


def _csv_response(rows: list[list], headers: list[str], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/risk-report")
def risk_report_csv(db: Session | None = Depends(get_db), _user: User = Depends(authority_only)):
    """Export all predictions as CSV."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    rows = (
        db.query(Prediction, GeographicData)
        .join(GeographicData, Prediction.geographic_id == GeographicData.id)
        .order_by(Prediction.predicted_at.desc())
        .all()
    )
    data = [
        [
            str(p.id),
            str(p.geographic_id),
            g.district_name,
            g.province,
            p.model_version,
            round(p.probability * 100, 2),
            p.risk_level,
            "; ".join(p.main_factors or []),
            "; ".join(p.recommendations or []),
            p.predicted_at.isoformat() if p.predicted_at else "",
            str(p.created_by) if p.created_by else "",
        ]
        for p, g in rows
    ]
    return _csv_response(
        data,
        [
            "prediction_id",
            "geographic_id",
            "district_name",
            "province",
            "model_version",
            "probability_pct",
            "risk_level",
            "main_factors",
            "recommendations",
            "predicted_at",
            "created_by",
        ],
        "risk_report.csv",
    )


@router.get("/historical-events")
def historical_events_csv(db: Session | None = Depends(get_db), _user: User = Depends(authority_only)):
    """Export historical flood events as CSV."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    rows = (
        db.query(FloodEvent, GeographicData)
        .join(GeographicData, FloodEvent.geographic_id == GeographicData.id)
        .order_by(FloodEvent.event_date.desc())
        .all()
    )
    data = [
        [
            str(e.id),
            g.district_name,
            g.province,
            e.event_date.isoformat(),
            e.rainfall_mm if e.rainfall_mm is not None else "",
            e.temperature_c if e.temperature_c is not None else "",
            e.humidity_pct if e.humidity_pct is not None else "",
            e.severity,
            e.flood_status,
            e.affected_population if e.affected_population is not None else "",
            e.source or "",
            e.damage_description or "",
        ]
        for e, g in rows
    ]
    return _csv_response(
        data,
        [
            "event_id",
            "district_name",
            "province",
            "event_date",
            "rainfall_mm",
            "temperature_c",
            "humidity_pct",
            "severity",
            "flood_status",
            "affected_population",
            "source",
            "damage_description",
        ],
        "historical_events.csv",
    )
