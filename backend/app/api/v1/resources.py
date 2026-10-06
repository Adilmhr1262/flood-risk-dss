"""Resource management for the authority command center.

- Shelter monitoring: capacity, current occupancy, availability, location.
- Response teams: create / update / deploy field teams.
- Emergency resources: rescue centres, hospitals and emergency facilities
  from the infrastructure registry.
All endpoints are authority-only.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import (
    TEAM_STATUSES,
    TEAM_TYPES,
    GeographicData,
    Infrastructure,
    ResponseTeam,
    Shelter,
    User,
    ROLE_AUTHORITY,
)
from app.schemas import (
    ResponseTeamCreate,
    ResponseTeamOut,
    ResponseTeamUpdate,
    ShelterResourceOut,
    ShelterUpdate,
)

router = APIRouter()

authority_only = require_role(ROLE_AUTHORITY)

SHELTER_STATUSES = ("open", "full", "closed", "maintenance")


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


def _point(geom) -> tuple[float | None, float | None]:
    if geom is None:
        return None, None
    shape = to_shape(geom)
    if shape.geom_type == "Point":
        return shape.coords[0][1], shape.coords[0][0]
    return None, None


# ---------------------------------------------------------------------------
# Shelters
# ---------------------------------------------------------------------------


@router.get("/shelters", response_model=list[ShelterResourceOut])
def list_shelters(
    district_name: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Shelter monitoring: capacity vs. occupancy, status, and location."""
    db = _db_or_503(db)
    query = (
        db.query(Shelter, GeographicData)
        .outerjoin(GeographicData, Shelter.geographic_id == GeographicData.id)
        .order_by(Shelter.name)
    )
    if district_name is not None:
        query = query.filter(GeographicData.district_name.ilike(f"%{district_name.strip()}%"))
    out = []
    for s, g in query.all():
        lat, lng = _point(s.geom)
        availability = None
        occupancy_pct = None
        if s.capacity is not None:
            availability = max(0, s.capacity - (s.current_occupancy or 0))
            occupancy_pct = round(100.0 * (s.current_occupancy or 0) / s.capacity, 1) if s.capacity > 0 else 0.0
        out.append(
            ShelterResourceOut(
                id=s.id,
                name=s.name,
                district_name=g.district_name if g else None,
                capacity=s.capacity,
                current_occupancy=s.current_occupancy or 0,
                availability=availability,
                occupancy_pct=occupancy_pct,
                status=s.status or "open",
                contact_phone=s.contact_phone,
                latitude=lat,
                longitude=lng,
            )
        )
    return out


@router.patch("/shelters/{shelter_id}", response_model=ShelterResourceOut)
def update_shelter(
    shelter_id: UUID,
    payload: ShelterUpdate,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """Update a shelter's occupancy and/or operational status."""
    db = _db_or_503(db)
    shelter = db.query(Shelter).filter(Shelter.id == shelter_id).first()
    if shelter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelter not found")
    if payload.status is not None:
        if payload.status not in SHELTER_STATUSES:
            raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(SHELTER_STATUSES)}")
        shelter.status = payload.status
    if payload.current_occupancy is not None:
        if shelter.capacity is not None and payload.current_occupancy > shelter.capacity:
            raise HTTPException(status_code=422, detail="Occupancy cannot exceed capacity")
        shelter.current_occupancy = payload.current_occupancy
        if shelter.capacity is not None:
            shelter.status = "full" if payload.current_occupancy >= shelter.capacity else (
                "open" if shelter.status == "full" else shelter.status
            )
    db.commit()
    db.refresh(shelter)
    return _shelter_out(db, shelter)


def _shelter_out(db: Session, s: Shelter) -> ShelterResourceOut:
    g = db.query(GeographicData).filter(GeographicData.id == s.geographic_id).first() if s.geographic_id else None
    lat, lng = _point(s.geom)
    availability = None
    occupancy_pct = None
    if s.capacity is not None:
        availability = max(0, s.capacity - (s.current_occupancy or 0))
        occupancy_pct = round(100.0 * (s.current_occupancy or 0) / s.capacity, 1) if s.capacity > 0 else 0.0
    return ShelterResourceOut(
        id=s.id,
        name=s.name,
        district_name=g.district_name if g else None,
        capacity=s.capacity,
        current_occupancy=s.current_occupancy or 0,
        availability=availability,
        occupancy_pct=occupancy_pct,
        status=s.status or "open",
        contact_phone=s.contact_phone,
        latitude=lat,
        longitude=lng,
    )


# ---------------------------------------------------------------------------
# Response teams
# ---------------------------------------------------------------------------


@router.get("/teams", response_model=list[ResponseTeamOut])
def list_teams(
    status: str | None = Query(default=None),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    db = _db_or_503(db)
    if status is not None and status not in TEAM_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(TEAM_STATUSES)}")
    query = db.query(ResponseTeam).order_by(ResponseTeam.name)
    if status is not None:
        query = query.filter(ResponseTeam.status == status)
    return [_team_out(db, t) for t in query.all()]


def _team_out(db: Session, t: ResponseTeam) -> ResponseTeamOut:
    g = db.query(GeographicData).filter(GeographicData.id == t.geographic_id).first() if t.geographic_id else None
    lat, lng = _point(t.geom)
    out = ResponseTeamOut.model_validate(t)
    out.district_name = g.district_name if g else None
    out.latitude = lat
    out.longitude = lng
    return out


@router.post("/teams", response_model=ResponseTeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: ResponseTeamCreate,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    db = _db_or_503(db)
    if payload.team_type not in TEAM_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown team type. Valid: {', '.join(TEAM_TYPES)}")
    if payload.status not in TEAM_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(TEAM_STATUSES)}")
    geographic_id = _resolve_geographic_id(db, payload.district_name) if payload.district_name else None
    geom = None
    if payload.latitude is not None and payload.longitude is not None:
        geom = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
    team = ResponseTeam(
        name=payload.name,
        team_type=payload.team_type,
        geographic_id=geographic_id,
        members_count=payload.members_count,
        status=payload.status,
        contact_phone=payload.contact_phone,
        geom=geom,
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return _team_out(db, team)


@router.patch("/teams/{team_id}", response_model=ResponseTeamOut)
def update_team(
    team_id: UUID,
    payload: ResponseTeamUpdate,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    db = _db_or_503(db)
    team = db.query(ResponseTeam).filter(ResponseTeam.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if payload.status is not None:
        if payload.status not in TEAM_STATUSES:
            raise HTTPException(status_code=422, detail=f"Unknown status. Valid: {', '.join(TEAM_STATUSES)}")
        team.status = payload.status
    if payload.members_count is not None:
        team.members_count = payload.members_count
    if payload.contact_phone is not None:
        team.contact_phone = payload.contact_phone
    if payload.district_name is not None:
        team.geographic_id = _resolve_geographic_id(db, payload.district_name)
    db.commit()
    db.refresh(team)
    return _team_out(db, team)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: UUID,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    db = _db_or_503(db)
    team = db.query(ResponseTeam).filter(ResponseTeam.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    db.delete(team)
    db.commit()


# ---------------------------------------------------------------------------
# Emergency infrastructure registry
# ---------------------------------------------------------------------------


@router.get("/infrastructure", response_model=list[dict])
def list_infrastructure(
    type: str | None = Query(default=None, description="hospital | rescue_center | emergency_facility"),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    """JSON view of the infrastructure registry for command-center tables."""
    db = _db_or_503(db)
    query = (
        db.query(Infrastructure, GeographicData)
        .outerjoin(GeographicData, Infrastructure.geographic_id == GeographicData.id)
        .order_by(Infrastructure.name)
    )
    if type is not None:
        query = query.filter(Infrastructure.type == type)
    rows = []
    for infra, g in query.all():
        lat, lng = _point(infra.geom)
        rows.append(
            {
                "id": str(infra.id),
                "name": infra.name,
                "type": infra.type,
                "district_name": g.district_name if g else None,
                "capacity": infra.capacity,
                "contact_phone": infra.contact_phone,
                "operational_status": infra.operational_status,
                "is_sample_data": infra.is_sample_data,
                "latitude": lat,
                "longitude": lng,
            }
        )
    return rows
