"""Administration endpoints: dataset imports (authority only)."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import (
    REPORT_CATEGORIES,
    REPORT_PRIORITIES,
    REPORT_STATUSES,
    ROLE_AUTHORITY,
    CitizenReport,
    GeographicData,
    User,
)
from app.schemas import (
    CitizenReportOut,
    CitizenReportVerify,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.services.importers import get_importer

router = APIRouter()

authority_only = require_role(ROLE_AUTHORITY)

# ~/workspace/flood-risk-dss/data/templates
TEMPLATE_DIR = Path(__file__).resolve().parents[4] / "datasets" / "templates"

UPLOAD_SUFFIXES = {
    "flood_events": {".csv"},
    "weather": {".csv"},
    "geographic": {".csv"},
    "boundaries": {".geojson", ".json"},
}


@router.post("/import/{dataset}")
async def import_dataset(
    dataset: str,
    file: UploadFile = File(...),
    dry_run: bool = False,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Upload a CSV/GeoJSON file and import it into the given dataset.

    Returns the import report (totals, duplicates skipped, per-row errors).
    With dry_run=true nothing is persisted.
    """
    importer_cls = get_importer(dataset)
    if importer_cls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown dataset '{dataset}'",
        )
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in UPLOAD_SUFFIXES[dataset]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected one of {sorted(UPLOAD_SUFFIXES[dataset])} "
                   f"for dataset '{dataset}'",
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        report = importer_cls().run(db, tmp_path, dry_run=dry_run)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return report.to_dict()


@router.get("/import/templates/{dataset}")
def download_template(
    dataset: str,
    _user: User = Depends(authority_only),
):
    """Download a sample import file (headers + example rows) for a dataset."""
    importer_cls = get_importer(dataset)
    if importer_cls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown dataset '{dataset}'",
        )
    filename = "boundaries.geojson" if dataset == "boundaries" else f"{dataset}.csv"
    path = TEMPLATE_DIR / filename
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No template available for dataset '{dataset}'",
        )
    media_type = "application/geo+json" if path.suffix == ".geojson" else "text/csv"
    return FileResponse(path, filename=filename, media_type=media_type)


# ---------------------------------------------------------------------------
# Citizen report triage (Phase 6 verification workflow)
# ---------------------------------------------------------------------------


@router.get("/reports", response_model=list[CitizenReportOut])
def list_reports(
    status: str | None = Query(default=None, description="Filter by report status"),
    category: str | None = Query(default=None, description="Filter by report category"),
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """List citizen reports for the authority triage queue, newest first."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    if status is not None and status not in REPORT_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(REPORT_STATUSES)}")
    if category is not None and category not in REPORT_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Unknown category. Valid: {', '.join(REPORT_CATEGORIES)}")
    query = (
        db.query(CitizenReport, GeographicData.district_name)
        .join(GeographicData, CitizenReport.geographic_id == GeographicData.id)
        .order_by(CitizenReport.created_at.desc())
    )
    if status is not None:
        query = query.filter(CitizenReport.status == status)
    if category is not None:
        query = query.filter(CitizenReport.category == category)
    if district_name is not None:
        query = query.filter(GeographicData.district_name.ilike(f"%{district_name.strip()}%"))
    out = []
    for report, dname in query.all():
        row = CitizenReportOut.model_validate(report)
        row.district_name = dname
        out.append(row)
    return out


@router.patch("/reports/{report_id}/verify", response_model=CitizenReportOut)
def verify_report(
    report_id: UUID,
    payload: CitizenReportVerify,
    db: Session | None = Depends(get_db),
    user: User = Depends(authority_only),
):
    """Authority triage decision: pending -> verified | rejected | resolved.

    Records who verified and when, so the verification chain is auditable.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    if payload.status not in REPORT_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(REPORT_STATUSES)}")
    if payload.priority is not None and payload.priority not in REPORT_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"Unknown priority. Valid: {', '.join(REPORT_PRIORITIES)}")
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report.status = payload.status
    if payload.priority is not None:
        report.priority = payload.priority
    report.verified_by = user.id
    report.verified_at = datetime.now(timezone.utc)
    report.verification_note = payload.note
    db.commit()
    db.refresh(report)
    out = CitizenReportOut.model_validate(report)
    district = db.query(GeographicData).filter(GeographicData.id == report.geographic_id).first()
    out.district_name = district.district_name if district else None
    return out


@router.get("/reports/map", response_model=GeoJSONFeatureCollection)
def reports_map(
    status: str | None = Query(default=None, description="Filter by report status"),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Authority-only GeoJSON layer of citizen reports for the command map."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    if status is not None and status not in REPORT_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(REPORT_STATUSES)}")
    query = (
        db.query(CitizenReport, GeographicData)
        .join(GeographicData, CitizenReport.geographic_id == GeographicData.id)
        .order_by(CitizenReport.created_at.desc())
    )
    if status is not None:
        query = query.filter(CitizenReport.status == status)
    features = []
    for report, g in query.all():
        coords = None
        if report.geom is not None:
            shape = to_shape(report.geom)
            if shape.geom_type == "Point":
                coords = [shape.coords[0][0], shape.coords[0][1]]
        features.append(
            GeoJSONFeature(
                geometry={"type": "Point", "coordinates": coords or [0.0, 0.0]},
                properties={
                    "report_id": str(report.id),
                    "district_name": g.district_name,
                    "category": report.category,
                    "severity": report.severity,
                    "status": report.status,
                    "priority": report.priority,
                    "description": (report.description or "")[:200],
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)
