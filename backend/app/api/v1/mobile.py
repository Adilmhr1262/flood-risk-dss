"""Mobile app endpoints: lightweight, community-focused views of the system.

All endpoints require a valid JWT (any role, including the Phase 5
``volunteer`` role). Payloads are trimmed for mobile bandwidth: no GeoJSON
wrapping, distances pre-computed, only the fields a phone screen needs.
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from geoalchemy2 import Geography, WKTElement
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import (
    REPORT_CATEGORIES,
    ROLE_AUTHORITY,
    ROLE_NGO,
    ROLE_PUBLIC,
    ROLE_VOLUNTEER,
    Alert,
    CitizenReport,
    DeviceToken,
    EmergencyContact,
    GeographicData,
    Prediction,
    Shelter,
    User,
)
from app.schemas import (
    CitizenReportCreate,
    CitizenReportOut,
    DeviceTokenCreate,
    DeviceTokenOut,
)

router = APIRouter()
all_roles = require_role(ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC, ROLE_VOLUNTEER)
# Citizen reporting is a community feature: volunteers, public users and NGO
# staff may submit field reports; authority accounts use the admin console.
reporter_roles = require_role(ROLE_NGO, ROLE_PUBLIC, ROLE_VOLUNTEER)


def _resolve_district(db: Session, district_name: str) -> GeographicData:
    row = (
        db.query(GeographicData)
        .filter(func.lower(GeographicData.district_name) == district_name.strip().lower())
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_name}' is not registered",
        )
    return row


def _nearest_district(db: Session, lat: float, lon: float) -> GeographicData:
    """District whose centroid is closest to the given GPS position."""
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)
    row = (
        db.query(GeographicData)
        .order_by(func.ST_Distance(GeographicData.geom, point))
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No districts registered"
        )
    return row


def _check_db(db):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")


@router.get("/my-risk")
def my_risk(
    district_name: str | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90.0, le=90.0),
    lon: float | None = Query(default=None, ge=-180.0, le=180.0),
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Latest stored risk assessment for a district.

    Pass ``?district_name=`` or a GPS fix (``?lat=&lon=``) to match the
    nearest district. Returns 404 when the district has no prediction yet —
    the app can then request a fresh assessment via POST /risk/predict.
    """
    _check_db(db)
    if district_name:
        district = _resolve_district(db, district_name)
    elif lat is not None and lon is not None:
        district = _nearest_district(db, lat, lon)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide ?district_name= or ?lat=&lon=",
        )
    prediction = (
        db.query(Prediction)
        .filter(Prediction.geographic_id == district.id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk assessment stored yet for '{district.district_name}'",
        )
    return {
        "district_name": district.district_name,
        "province": district.province,
        "risk_level": prediction.risk_level,
        "probability": round(prediction.probability * 100, 2),
        "main_factors": list(prediction.main_factors or []),
        "recommendations": list(prediction.recommendations or []),
        "model_version": prediction.model_version,
        "updated_at": prediction.predicted_at.isoformat() if prediction.predicted_at else None,
    }


@router.get("/alerts")
def mobile_alerts(
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Active public alerts, newest first, optionally filtered by district."""
    _check_db(db)
    query = db.query(Alert, GeographicData).outerjoin(
        GeographicData, Alert.geographic_id == GeographicData.id
    )
    query = query.filter(Alert.is_active.is_(True)).order_by(Alert.issued_at.desc())
    if district_name:
        query = query.filter(GeographicData.district_name.ilike(f"%{district_name.strip()}%"))
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "message": a.message,
            "severity": a.severity,
            "district_name": g.district_name if g else None,
            "issued_at": a.issued_at.isoformat() if a.issued_at else None,
        }
        for a, g in query.all()
    ]


@router.get("/shelters/nearby")
def shelters_nearby(
    lat: float = Query(ge=-90.0, le=90.0),
    lon: float = Query(ge=-180.0, le=180.0),
    radius_km: float = Query(default=50.0, gt=0.0, le=500.0),
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Shelters within ``radius_km`` of a GPS position, nearest first.

    Distances are geodesic (geography cast, km). Shelters without their own
    geometry fall back to their district centroid.
    """
    _check_db(db)
    user_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    shelter_geom = func.coalesce(Shelter.geom, GeographicData.geom)
    distance_km = (
        func.ST_Distance(
            func.cast(shelter_geom, Geography),
            func.cast(user_point, Geography),
        )
        / 1000.0
    )
    rows = (
        db.query(Shelter, GeographicData, distance_km.label("distance_km"))
        .outerjoin(GeographicData, Shelter.geographic_id == GeographicData.id)
        .filter(distance_km <= radius_km)
        .order_by(distance_km)
        .all()
    )
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "district_name": g.district_name if g else None,
            "distance_km": round(float(dist), 2),
            "capacity": s.capacity,
            "facilities": list(s.facilities or []),
            "contact_phone": s.contact_phone,
        }
        for s, g, dist in rows
    ]


@router.get("/emergency-contacts")
def mobile_emergency_contacts(
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Rescue / relief contact directory, optionally filtered by district."""
    _check_db(db)
    query = db.query(EmergencyContact).order_by(EmergencyContact.organization, EmergencyContact.name)
    if district_name:
        query = query.filter(EmergencyContact.district_name.ilike(f"%{district_name.strip()}%"))
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "organization": c.organization,
            "phone": c.phone,
            "district_name": c.district_name,
        }
        for c in query.all()
    ]


@router.post("/report-event", response_model=CitizenReportOut, status_code=status.HTTP_201_CREATED)
def report_event(
    payload: CitizenReportCreate,
    db: Session | None = Depends(get_db),
    user: User = Depends(reporter_roles),
):
    """Submit a community flood sighting report.

    Volunteer, public and NGO users may report. Reports start as
    ``pending`` and are triaged by authority users through the verification
    workflow (pending -> verified | rejected | resolved).
    """
    _check_db(db)
    if payload.category is not None and payload.category not in REPORT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown category '{payload.category}'. Valid: {', '.join(REPORT_CATEGORIES)}",
        )
    district = _resolve_district(db, payload.district_name)
    report = CitizenReport(
        reporter_id=user.id,
        geographic_id=district.id,
        geom=WKTElement(f"POINT({payload.lon} {payload.lat})", srid=4326),
        severity=payload.severity,
        description=payload.description,
        category=payload.category,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    out = CitizenReportOut.model_validate(report)
    out.district_name = district.district_name
    return out


UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "reports"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


@router.post("/report-event/{report_id}/image")
def upload_report_image(
    report_id: UUID,
    file: UploadFile = File(...),
    db: Session | None = Depends(get_db),
    user: User = Depends(all_roles),
):
    """Attach a photo to a citizen report.

    The reporter (or any authority user) may upload. Only jpg/png/webp up to
    5 MB are accepted; files are stored under backend/uploads/reports/.
    """
    _check_db(db)
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.reporter_id != user.id and user.role != ROLE_AUTHORITY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the reporter or an authority user may attach images",
        )
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported image type '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)}",
        )
    data = file.file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {MAX_IMAGE_BYTES // (1024 * 1024)} MB",
        )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{report_id}{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    report.image_path = f"uploads/reports/{filename}"
    db.commit()
    return {"report_id": str(report_id), "image_path": report.image_path}


@router.post("/device-token", response_model=DeviceTokenOut, status_code=status.HTTP_201_CREATED)
def register_device_token(
    payload: DeviceTokenCreate,
    db: Session | None = Depends(get_db),
    user: User = Depends(all_roles),
):
    """Register an FCM device token for push warnings."""
    _check_db(db)
    existing = db.query(DeviceToken).filter(DeviceToken.fcm_token == payload.fcm_token).first()
    if existing is not None:
        existing.user_id = user.id
        existing.platform = payload.platform
        db.commit()
        db.refresh(existing)
        return existing
    token = DeviceToken(user_id=user.id, fcm_token=payload.fcm_token, platform=payload.platform)
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


@router.delete("/device-token", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device_token(
    fcm_token: str = Query(min_length=10, max_length=512),
    db: Session | None = Depends(get_db),
    user: User = Depends(all_roles),
):
    """Remove an FCM device token (logout / opt-out)."""
    _check_db(db)
    db.query(DeviceToken).filter(
        DeviceToken.fcm_token == fcm_token, DeviceToken.user_id == user.id
    ).delete()
    db.commit()
    return None


@router.get("/reports/mine")
def my_reports(
    db: Session | None = Depends(get_db),
    user: User = Depends(all_roles),
):
    """Flood sighting reports submitted by the current user, newest first."""
    _check_db(db)
    rows = (
        db.query(CitizenReport, GeographicData)
        .join(GeographicData, CitizenReport.geographic_id == GeographicData.id)
        .filter(CitizenReport.reporter_id == user.id)
        .order_by(CitizenReport.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "district_name": g.district_name,
            "severity": r.severity,
            "description": r.description,
            "status": r.status,
            "category": r.category,
            "image_path": r.image_path,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r, g in rows
    ]
