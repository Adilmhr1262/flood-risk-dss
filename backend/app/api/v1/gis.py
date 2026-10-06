"""GIS layers: district risk points, historical flood events, shelters,
emergency contacts, district attributes and (optional) district boundaries
as GeoJSON.

Locations come from the geographic_data table (PostGIS, SRID 4326); shelters
carry their own geometry with a fallback to the linked district centroid.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import to_shape
from sqlalchemy import func, inspect
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.db.session import engine
from app.models import (
    EmergencyContact,
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
from app.schemas import GeoJSONFeature, GeoJSONFeatureCollection

router = APIRouter()
all_roles = require_role(ROLE_AUTHORITY, ROLE_NGO, ROLE_PUBLIC)

RISK_COLORS = {"LOW": "#2ecc71", "MEDIUM": "#f1c40f", "HIGH": "#e74c3c"}
PRIORITY_COLORS = {"LOW": "#2ecc71", "MEDIUM": "#f1c40f", "HIGH": "#e67e22", "CRITICAL": "#e74c3c"}

SEVERITY_LABELS = {1: "Minor", 2: "Moderate", 3: "Severe", 4: "Very severe", 5: "Catastrophic"}


def _priority_class(risk_level: str | None, vulnerability_index: float | None) -> str:
    """Decision priority from the latest risk level and vulnerability index.

    Methodology (documented in docs/gis-module.md):
    - CRITICAL: HIGH risk and vulnerability_index >= 0.33
    - HIGH: HIGH risk, or vulnerability_index >= 0.40
    - MEDIUM: MEDIUM risk, or vulnerability_index >= 0.25
    - LOW: everything else
    """
    v = vulnerability_index or 0.0
    if risk_level == "HIGH" and v >= 0.33:
        return "CRITICAL"
    if risk_level == "HIGH" or v >= 0.40:
        return "HIGH"
    if risk_level == "MEDIUM" or v >= 0.25:
        return "MEDIUM"
    return "LOW"


def _point_geometry(wkb_element, fallback_wkb=None) -> dict[str, Any]:
    """Convert a PostGIS geometry element to a GeoJSON geometry dict."""
    element = wkb_element if wkb_element is not None else fallback_wkb
    if element is None:
        return {"type": "Point", "coordinates": [0.0, 0.0]}
    shape = to_shape(element)
    coords = list(shape.coords)[0] if shape.geom_type == "Point" else None
    if coords is None:  # pragma: no cover - defensive
        return {"type": "Point", "coordinates": [0.0, 0.0]}
    return {"type": "Point", "coordinates": [coords[0], coords[1]]}


def _latest_predictions_subquery(db):
    """One row per geographic_id: the most recent prediction timestamp."""
    return (
        db.query(Prediction.geographic_id, func.max(Prediction.predicted_at).label("latest"))
        .group_by(Prediction.geographic_id)
        .subquery()
    )


@router.get("/risk-layers", response_model=GeoJSONFeatureCollection)
def risk_layers(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """GeoJSON FeatureCollection of assessment points with their latest assessed risk level."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")

    sub = _latest_predictions_subquery(db)
    rows = (
        db.query(Prediction, GeographicData)
        .join(GeographicData, Prediction.geographic_id == GeographicData.id)
        .join(sub, (Prediction.geographic_id == sub.c.geographic_id) & (Prediction.predicted_at == sub.c.latest))
        .all()
    )

    features = []
    for p, g in rows:
        features.append(
            GeoJSONFeature(
                geometry={"type": "Point", "coordinates": [g.longitude, g.latitude]},
                properties={
                    "geographic_id": str(g.id),
                    "district_name": g.district_name,
                    "province": g.province,
                    "risk_level": p.risk_level,
                    "probability": round(p.probability * 100, 2),
                    "color": RISK_COLORS.get(p.risk_level, "#95a5a6"),
                    "model_version": p.model_version,
                    "main_factors": list(p.main_factors or []),
                    "predicted_at": p.predicted_at.isoformat() if p.predicted_at else None,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/historical-layers", response_model=GeoJSONFeatureCollection)
def historical_layers(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """GeoJSON FeatureCollection of historical flood event locations."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    rows = (
        db.query(FloodEvent, GeographicData)
        .join(GeographicData, FloodEvent.geographic_id == GeographicData.id)
        .order_by(FloodEvent.event_date.desc())
        .all()
    )

    features = []
    for e, g in rows:
        features.append(
            GeoJSONFeature(
                geometry={"type": "Point", "coordinates": [g.longitude, g.latitude]},
                properties={
                    "event_id": str(e.id),
                    "district_name": g.district_name,
                    "province": g.province,
                    "event_date": e.event_date.isoformat(),
                    "rainfall_mm": e.rainfall_mm,
                    "temperature_c": e.temperature_c,
                    "humidity_pct": e.humidity_pct,
                    "severity": e.severity,
                    "flood_status": e.flood_status,
                    "affected_population": e.affected_population,
                    "source": e.source,
                    "damage_description": e.damage_description,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/shelters", response_model=GeoJSONFeatureCollection)
def shelter_layer(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """GeoJSON FeatureCollection of emergency shelter / relief camp locations."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    rows = (
        db.query(Shelter, GeographicData)
        .outerjoin(GeographicData, Shelter.geographic_id == GeographicData.id)
        .order_by(Shelter.name)
        .all()
    )
    features = []
    for s, g in rows:
        geometry = _point_geometry(s.geom, g.geom if g is not None else None)
        features.append(
            GeoJSONFeature(
                geometry=geometry,
                properties={
                    "shelter_id": str(s.id),
                    "name": s.name,
                    "district_name": g.district_name if g else None,
                    "province": g.province if g else None,
                    "capacity": s.capacity,
                    "facilities": list(s.facilities or []),
                    "contact_phone": s.contact_phone,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/emergency-contacts")
def emergency_contact_layer(
    district_name: str | None = None,
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Emergency rescue / relief contact directory, optionally filtered by district."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
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


@router.get("/districts", response_model=GeoJSONFeatureCollection)
def district_layer(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """GeoJSON FeatureCollection of all registered districts with full attributes."""
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    rows = db.query(GeographicData).order_by(GeographicData.province, GeographicData.district_name).all()
    features = []
    for g in rows:
        features.append(
            GeoJSONFeature(
                geometry=_point_geometry(g.geom),
                properties={
                    "geographic_id": str(g.id),
                    "district_name": g.district_name,
                    "province": g.province,
                    "latitude": g.latitude,
                    "longitude": g.longitude,
                    "elevation_m": g.elevation_m,
                    "river_distance_km": g.river_distance_km,
                    "slope_deg": g.slope_deg,
                    "population_density_per_km2": g.population_density_per_km2,
                    "vulnerability_index": g.vulnerability_index,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/boundaries", response_model=GeoJSONFeatureCollection)
def boundary_layer(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """GeoJSON FeatureCollection of district boundary polygons.

    Served from the ``district_boundaries`` table when the migration that
    creates it has been applied; otherwise returns 404 with a clear message.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    inspector = inspect(engine)
    if "district_boundaries" not in inspector.get_table_names():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="District boundaries are not loaded yet (district_boundaries table missing). "
                   "Apply the boundaries migration to enable this layer.",
        )
    from sqlalchemy import MetaData, Table

    table = Table("district_boundaries", MetaData(), autoload_with=engine)
    columns = {c.name: c for c in table.columns}
    geom_col = next((c for c in table.columns if "geometry" in str(c.type).lower() or "geography" in str(c.type).lower()), None)
    if geom_col is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="district_boundaries has no geometry column")
    name_candidates = ["district_name", "name", "district", "label"]
    name_col = next((columns[n] for n in name_candidates if n in columns), None)

    rows = db.execute(
        table.select().with_only_columns(
            table.c[name_col.name] if name_col is not None else table.columns[0],
            func.ST_AsGeoJSON(geom_col).label("geojson"),
        )
    ).all()
    features = []
    for label, geojson in rows:
        geometry = json.loads(geojson) if geojson else {"type": "MultiPolygon", "coordinates": []}
        features.append(GeoJSONFeature(geometry=geometry, properties={"district_name": label}))
    return GeoJSONFeatureCollection(features=features)


# ---------------------------------------------------------------------------
# Phase 4 — advanced GIS intelligence layers
# ---------------------------------------------------------------------------

@router.get("/risk-layer", response_model=GeoJSONFeatureCollection)
def risk_layer(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """Current per-district risk: one feature per registered district.

    Unlike ``/risk-layers`` (assessment points, only districts with a stored
    prediction), this layer covers every district; districts without a
    prediction are marked ``NO_DATA``.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")

    sub = _latest_predictions_subquery(db)
    rows = (
        db.query(GeographicData, Prediction)
        .outerjoin(sub, GeographicData.id == sub.c.geographic_id)
        .outerjoin(
            Prediction,
            (Prediction.geographic_id == sub.c.geographic_id)
            & (Prediction.predicted_at == sub.c.latest),
        )
        .order_by(GeographicData.district_name)
        .all()
    )
    features = []
    for g, p in rows:
        risk_level = p.risk_level if p else "NO_DATA"
        features.append(
            GeoJSONFeature(
                geometry=_point_geometry(g.geom),
                properties={
                    "geographic_id": str(g.id),
                    "district_name": g.district_name,
                    "province": g.province,
                    "risk_level": risk_level,
                    "probability": round(p.probability * 100, 2) if p else None,
                    "color": RISK_COLORS.get(risk_level, "#95a5a6"),
                    "model_version": p.model_version if p else None,
                    "predicted_at": p.predicted_at.isoformat() if p and p.predicted_at else None,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/historical-floods", response_model=GeoJSONFeatureCollection)
def historical_floods(
    district_name: str | None = None,
    from_year: int | None = None,
    to_year: int | None = None,
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Historical flood events with decision-relevant properties.

    Richer sibling of ``/historical-layers``: adds year, severity label,
    affected population and source; filterable by district and year range.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    query = (
        db.query(FloodEvent, GeographicData)
        .join(GeographicData, FloodEvent.geographic_id == GeographicData.id)
        .order_by(FloodEvent.event_date.desc())
    )
    if district_name:
        query = query.filter(GeographicData.district_name.ilike(f"%{district_name.strip()}%"))
    if from_year:
        query = query.filter(func.extract("year", FloodEvent.event_date) >= from_year)
    if to_year:
        query = query.filter(func.extract("year", FloodEvent.event_date) <= to_year)

    features = []
    for e, g in query.all():
        year = e.event_date.year if e.event_date else None
        features.append(
            GeoJSONFeature(
                geometry=_point_geometry(g.geom),
                properties={
                    "event_id": str(e.id),
                    "district_name": g.district_name,
                    "province": g.province,
                    "event_date": e.event_date.isoformat() if e.event_date else None,
                    "year": year,
                    "severity": e.severity,
                    "severity_label": SEVERITY_LABELS.get(e.severity, "Unknown"),
                    "rainfall_mm": e.rainfall_mm,
                    "affected_population": e.affected_population,
                    "flood_status": e.flood_status,
                    "source": e.source,
                    "damage_description": e.damage_description,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/vulnerability-map", response_model=GeoJSONFeatureCollection)
def vulnerability_map(db: Session | None = Depends(get_db), _user: User = Depends(all_roles)):
    """District vulnerability as GeoJSON.

    Each feature carries population density, the composite vulnerability
    index (see data/processed/DATA_CARD.md), the latest risk level and the
    computed decision priority class (CRITICAL/HIGH/MEDIUM/LOW).
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")

    sub = _latest_predictions_subquery(db)
    rows = (
        db.query(GeographicData, VulnerabilityIndicator, Prediction)
        .outerjoin(VulnerabilityIndicator, VulnerabilityIndicator.geographic_id == GeographicData.id)
        .outerjoin(sub, GeographicData.id == sub.c.geographic_id)
        .outerjoin(
            Prediction,
            (Prediction.geographic_id == sub.c.geographic_id)
            & (Prediction.predicted_at == sub.c.latest),
        )
        .order_by(GeographicData.district_name)
        .all()
    )
    features = []
    for g, v, p in rows:
        vuln_index = v.vulnerability_index if v else g.vulnerability_index
        risk_level = p.risk_level if p else None
        priority = _priority_class(risk_level, vuln_index)
        features.append(
            GeoJSONFeature(
                geometry=_point_geometry(g.geom),
                properties={
                    "geographic_id": str(g.id),
                    "district_name": g.district_name,
                    "province": g.province,
                    "population_density": v.population_density if v else g.population_density_per_km2,
                    "vulnerability_index": round(vuln_index, 4) if vuln_index is not None else None,
                    "risk_level": risk_level,
                    "priority": priority,
                    "color": PRIORITY_COLORS[priority],
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)


@router.get("/infrastructure", response_model=GeoJSONFeatureCollection)
def infrastructure_layer(
    type: str | None = None,
    district_name: str | None = None,
    db: Session | None = Depends(get_db),
    _user: User = Depends(all_roles),
):
    """Critical infrastructure points: hospitals, rescue centres, emergency facilities.

    Filter with ``?type=hospital|rescue_center|emergency_facility|shelter`` and
    ``?district_name=``. Rows flagged ``is_sample_data`` are illustrative and
    must be replaced with authoritative registries before operational use.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    query = (
        db.query(Infrastructure, GeographicData)
        .outerjoin(GeographicData, Infrastructure.geographic_id == GeographicData.id)
        .order_by(Infrastructure.type, Infrastructure.name)
    )
    if type:
        query = query.filter(Infrastructure.type == type.strip().lower())
    if district_name:
        query = query.filter(GeographicData.district_name.ilike(f"%{district_name.strip()}%"))

    features = []
    for infra, g in query.all():
        features.append(
            GeoJSONFeature(
                geometry=_point_geometry(infra.geom, g.geom if g is not None else None),
                properties={
                    "infrastructure_id": str(infra.id),
                    "name": infra.name,
                    "type": infra.type,
                    "district_name": g.district_name if g else None,
                    "province": g.province if g else None,
                    "capacity": infra.capacity,
                    "contact_phone": infra.contact_phone,
                    "operational_status": infra.operational_status,
                    "is_sample_data": infra.is_sample_data,
                },
            )
        )
    return GeoJSONFeatureCollection(features=features)
