"""Operational incident management for the authority command center.

Incidents follow a controlled workflow:
detected -> verified -> response_started -> resolved.
All endpoints are authority-only.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import (
    INCIDENT_SOURCES,
    INCIDENT_STATUSES,
    INCIDENT_TRANSITIONS,
    GeographicData,
    Incident,
    IncidentNote,
    User,
    ROLE_AUTHORITY,
)
from app.schemas import (
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    IncidentCreate,
    IncidentNoteCreate,
    IncidentNoteOut,
    IncidentOut,
    IncidentStats,
    IncidentStatusUpdate,
)

router = APIRouter()

authority_only = require_role(ROLE_AUTHORITY)


def _db_or_503(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return db


def _resolve_geographic_id(db: Session, district_name: str) -> UUID:
    row = (
        db.query(GeographicData)
        .filter(func.lower(GeographicData.district_name) == district_name.strip().lower())
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_name}' is not registered in geographic_data",
        )
    return row.id


def _to_out(incident: Incident, db: Session) -> IncidentOut:
    district = None
    if incident.geographic_id is not None:
        district = db.query(GeographicData).filter(GeographicData.id == incident.geographic_id).first()
    out = IncidentOut.model_validate(incident)
    out.district_name = district.district_name if district else None
    return out


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status: str | None = Query(default=None, description=f"One of: {', '.join(INCIDENT_STATUSES)}"),
    district_name: str | None = Query(default=None),
    severity: int | None = Query(default=None, ge=1, le=5),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """List incidents, newest first, with optional filters."""
    db = _db_or_503(db)
    if status is not None and status not in INCIDENT_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(INCIDENT_STATUSES)}")
    query = db.query(Incident).order_by(Incident.created_at.desc())
    if status is not None:
        query = query.filter(Incident.status == status)
    if severity is not None:
        query = query.filter(Incident.severity == severity)
    if district_name is not None:
        query = query.join(GeographicData, Incident.geographic_id == GeographicData.id).filter(
            GeographicData.district_name.ilike(f"%{district_name.strip()}%")
        )
    return [_to_out(i, db) for i in query.all()]


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    db: Session | None = Depends(get_db),
    user: User = Depends(authority_only),
):
    """Raise a new incident. Starts in the 'detected' state."""
    db = _db_or_503(db)
    if payload.source not in INCIDENT_SOURCES:
        raise HTTPException(status_code=422, detail=f"Unknown source. Valid: {', '.join(INCIDENT_SOURCES)}")
    geographic_id = None
    if payload.district_name:
        geographic_id = _resolve_geographic_id(db, payload.district_name)
    geom = None
    if payload.latitude is not None and payload.longitude is not None:
        geom = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
    incident = Incident(
        title=payload.title,
        description=payload.description,
        geographic_id=geographic_id,
        geom=geom,
        status="detected",
        severity=payload.severity,
        source=payload.source,
        source_id=payload.source_id,
        created_by=user.id,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return _to_out(incident, db)


@router.get("/stats", response_model=IncidentStats)
def incident_stats(
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Response statistics: counts by status/severity and resolution timing."""
    db = _db_or_503(db)
    by_status = {s: 0 for s in INCIDENT_STATUSES}
    for s, n in db.query(Incident.status, func.count()).group_by(Incident.status).all():
        by_status[s] = n
    open_by_severity = {str(i): 0 for i in range(1, 6)}
    for sev, n in (
        db.query(Incident.severity, func.count())
        .filter(Incident.status != "resolved")
        .group_by(Incident.severity)
        .all()
    ):
        open_by_severity[str(sev)] = n
    resolved = (
        db.query(Incident.created_at, Incident.resolved_at)
        .filter(Incident.status == "resolved", Incident.resolved_at.is_not(None))
        .all()
    )
    avg_hours = None
    if resolved:
        avg_hours = sum((r - c).total_seconds() / 3600 for c, r in resolved) / len(resolved)
    week_ago = datetime.now(timezone.utc).timestamp() - 7 * 86400
    resolved_7d = sum(1 for _, r in resolved if r.timestamp() >= week_ago)
    return IncidentStats(
        by_status=by_status,
        open_by_severity=open_by_severity,
        avg_hours_to_resolve=avg_hours,
        resolved_last_7d=resolved_7d,
    )


@router.get("/map", response_model=GeoJSONFeatureCollection)
def incident_map(
    active_only: bool = Query(default=True),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Authority-only GeoJSON layer of incidents for the command map."""
    db = _db_or_503(db)
    query = db.query(Incident, GeographicData).outerjoin(
        GeographicData, Incident.geographic_id == GeographicData.id
    )
    if active_only:
        query = query.filter(Incident.status != "resolved")
    features = []
    for incident, g in query.order_by(Incident.created_at.desc()).all():
        coords = None
        if incident.geom is not None:
            shape = to_shape(incident.geom)
            if shape.geom_type == "Point":
                coords = [shape.coords[0][0], shape.coords[0][1]]
        features.append(
            GeoJSONFeature(
                geometry={"type": "Point", "coordinates": coords or [0.0, 0.0]},
                properties={
                    "incident_id": str(incident.id),
                    "title": incident.title,
                    "status": incident.status,
                    "severity": incident.severity,
                    "source": incident.source,
                    "district_name": g.district_name if g else None,
                    "created_at": incident.created_at.isoformat() if incident.created_at else None,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: UUID,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    db = _db_or_503(db)
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return _to_out(incident, db)


@router.patch("/{incident_id}/status", response_model=IncidentOut)
def update_incident_status(
    incident_id: UUID,
    payload: IncidentStatusUpdate,
    db: Session | None = Depends(get_db),
    user: User = Depends(authority_only),
):
    """Advance (or hold) an incident's workflow status.

    Only forward transitions are allowed:
    detected -> verified -> response_started -> resolved.
    An optional note is appended to the incident timeline.
    """
    db = _db_or_503(db)
    if payload.status not in INCIDENT_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(INCIDENT_STATUSES)}")
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if payload.status not in INCIDENT_TRANSITIONS[incident.status] and payload.status != incident.status:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition from '{incident.status}' to '{payload.status}'. "
            f"Allowed: {', '.join(INCIDENT_TRANSITIONS[incident.status]) or 'none'}",
        )
    incident.status = payload.status
    if payload.status == "resolved":
        incident.resolved_at = datetime.now(timezone.utc)
    if payload.note:
        db.add(IncidentNote(incident_id=incident.id, author_id=user.id, note=payload.note))
    db.commit()
    db.refresh(incident)
    return _to_out(incident, db)


@router.post("/{incident_id}/notes", response_model=IncidentNoteOut, status_code=status.HTTP_201_CREATED)
def add_incident_note(
    incident_id: UUID,
    payload: IncidentNoteCreate,
    db: Session | None = Depends(get_db),
    user: User = Depends(authority_only),
):
    db = _db_or_503(db)
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    note = IncidentNote(incident_id=incident.id, author_id=user.id, note=payload.note)
    db.add(note)
    db.commit()
    db.refresh(note)
    return IncidentNoteOut.model_validate(note)
