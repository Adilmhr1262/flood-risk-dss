"""FastAPI dependencies: database session and role-based access."""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models import User, VALID_ROLES

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Optional[Session]:
    """Yield a database session.

    If the database is unreachable, yield None instead of raising at import
    time. Every endpoint that needs persistence must check for None and return
    a 503 with a clear message. The risk engine and ML pipeline do not require
    a database connection.
    """
    db = None
    try:
        db = SessionLocal()
    except Exception:
        # Database unreachable at session-creation time: signal the
        # graceful fallback instead of raising at import/request time.
        yield None
        return
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session | None = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    payload = decode_token(credentials.credentials)
    if payload is None or "sub" not in payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*allowed: str):
    """Dependency factory enforcing role-based access control."""
    invalid = [r for r in allowed if r not in VALID_ROLES]
    if invalid:
        raise ValueError(f"Unknown role(s): {invalid}")

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource",
            )
        return user

    return checker
