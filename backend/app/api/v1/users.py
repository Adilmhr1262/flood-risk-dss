"""User management endpoints (authority role only)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models import User, ROLE_AUTHORITY, VALID_ROLES
from app.schemas import UserOut, UserUpdate
from app.schemas.common import Pagination, PaginatedResponse

router = APIRouter()
authority_only = require_role(ROLE_AUTHORITY)


@router.get("", response_model=PaginatedResponse)
def list_users(
    pagination: Pagination = Depends(),
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    query = db.query(User).order_by(User.id)
    total = query.count()
    rows = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).all()
    return PaginatedResponse(
        items=[UserOut.model_validate(r).model_dump() for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{id}", response_model=UserOut)
def get_user(id: UUID, db: Session | None = Depends(get_db), _user: User = Depends(authority_only)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    row = db.query(User).filter(User.id == id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return row


@router.patch("/{id}", response_model=UserOut)
def update_user(
    id: UUID,
    payload: UserUpdate,
    db: Session | None = Depends(get_db),
    _user: User = Depends(authority_only),
):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    row = db.query(User).filter(User.id == id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    data = payload.model_dump(exclude_unset=True)
    if "role" in data and data["role"] not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role")
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: UUID, db: Session | None = Depends(get_db), _user: User = Depends(authority_only)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    row = db.query(User).filter(User.id == id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(row)
    db.commit()
