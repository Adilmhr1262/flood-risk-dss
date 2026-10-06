"""Authentication endpoints: registration, login, token refresh, profile.

Token model is stateless JWT: login/register issue an access + refresh pair.
Clients keep the refresh token and call POST /auth/refresh before the access
token expires. Logout is client-side (discard both tokens); POST /auth/logout
exists as a documented no-op for client state machines.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    decode_refresh_token,
    hash_password,
    issue_token_pair,
    verify_password,
)
from app.models import User, VALID_ROLES
from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter()


def _token_pair_for(user: User) -> TokenResponse:
    access, refresh = issue_token_pair(str(user.id), user.role)
    return TokenResponse(access_token=access, refresh_token=refresh, role=user.role)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session | None = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    role = payload.role if payload.role in VALID_ROLES else "public"
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        location_name=payload.location_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_pair_for(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session | None = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _token_pair_for(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session | None = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh pair.

    Returns 401 when the refresh token is missing, expired, malformed, not a
    refresh-type token, or belongs to a user that no longer exists.
    """
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    claims = decode_refresh_token(payload.refresh_token)
    if claims is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user = db.query(User).filter(User.id == claims["sub"]).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return _token_pair_for(user)


@router.post("/logout")
def logout():
    """Stateless logout: tokens are JWTs and are not stored server-side.

    Clients must discard both the access and the refresh token. Documented
    here so client implementations have an explicit lifecycle endpoint.
    """
    return {"message": "Logged out. Discard the access and refresh tokens on the client."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


__all__ = ["router"]
