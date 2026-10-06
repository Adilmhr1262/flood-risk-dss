"""Security helpers: password hashing and JWT handling.

Two token types are issued on login/register:
- access token  (``type="access"``, short-lived) — authorizes API calls.
- refresh token (``type="refresh"``, long-lived) — exchanged at
  ``POST /auth/refresh`` for a fresh access token; it never authorizes
  regular API endpoints (``get_current_user`` rejects it).
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _encode(subject: str, role: str, token_type: str, expires: datetime) -> str:
    payload = {"sub": subject, "role": role, "type": token_type, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return _encode(subject, role, "access", expires)


def create_refresh_token(subject: str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return _encode(subject, role, "refresh", expires)


def issue_token_pair(subject: str, role: str) -> tuple[str, str]:
    """Return (access_token, refresh_token) for a successful login/register."""
    return create_access_token(subject, role), create_refresh_token(subject, role)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    """Decode and validate a refresh token; return payload or None."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh" or "sub" not in payload:
        return None
    return payload
