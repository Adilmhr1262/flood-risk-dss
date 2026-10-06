"""Flood alert management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import ALERT_SEVERITIES, Alert, GeographicData, User, ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC
from app.schemas import AlertCreate, AlertOut
from app.schemas.common import PaginatedResponse, Pagination

router = APIRouter()

staff_only = require_role(ROLE_AUTHORITY, ROLE_NGO)
all_roles = require_role(ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC)


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


@router.get("", response_model=PaginatedResponse)
def list_alerts(
    active_only: bool = False,
    pagination: Pagination = Depends(),
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    query = db.query(Alert).order_by(Alert.issued_at.desc())
    if active_only:
        query = query.filter(Alert.is_active.is_(True))
    total = query.count()
    rows = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).all()
    items = [AlertOut.model_validate(r).model_dump() for r in rows]
    return PaginatedResponse(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: Session | None = Depends(get_db), _user: User = Depends(staff_only)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    severity = payload.severity if payload.severity in ALERT_SEVERITIES else "info"
    row = Alert(
        geographic_id=_resolve_geographic_id(db, payload.district_name),
        title=payload.title,
        message=payload.message,
        severity=severity,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AlertOut.model_validate(row)


@router.patch("/{id}/deactivate", response_model=AlertOut)
def deactivate_alert(id: UUID, db: Session | None = Depends(get_db), _user: User = Depends(staff_only)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    row = db.query(Alert).filter(Alert.id == id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    row.is_active = False
    db.commit()
    db.refresh(row)
    return AlertOut.model_validate(row)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(id: UUID, db: Session | None = Depends(get_db), _user: User = Depends(staff_only)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    row = db.query(Alert).filter(Alert.id == id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    db.delete(row)
    db.commit()
