"""In-memory sliding-window rate limiter (per client IP).

Stricter budget for authentication endpoints (credential-stuffing
protection), a general budget for everything else. Counters live in the
process memory: on a multi-worker deployment each worker enforces its own
budget, which is the standard trade-off for a dependency-free limiter.
For a stricter global budget, front the API with a reverse proxy
(see docs/deployment-guide.md) and rate-limit there.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings


class _SlidingWindow:
    """Per-key request timestamps with a fixed window."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = {}

    def allowed(self, key: str) -> Tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        hits = self._hits.setdefault(key, deque())
        cutoff = now - self.window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.limit:
            retry_after = int(hits[0] + self.window - now) + 1
            return False, max(retry_after, 1)
        hits.append(now)
        # Opportunistic cleanup so the dict cannot grow without bound.
        if len(self._hits) > 10000:
            stale = [k for k, v in self._hits.items() if not v or v[-1] <= cutoff]
            for k in stale:
                del self._hits[k]
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests over the per-IP budget with HTTP 429.

    Budgets are read from settings on every request (not cached at
    startup) so tests can raise them without rebuilding the app.
    """

    def __init__(self, app, auth_paths: Tuple[str, ...] = ("/api/v1/auth/",)) -> None:
        super().__init__(app)
        self.auth_paths = auth_paths
        self._limiters: Dict[str, _SlidingWindow] = {}

    def _limiter(self, name: str, limit: int) -> _SlidingWindow:
        limiter = self._limiters.get(name)
        if limiter is None or limiter.limit != limit:
            limiter = _SlidingWindow(limit)
            self._limiters[name] = limiter
        return limiter

    def _client_ip(self, request: Request) -> str:
        # When behind the documented nginx reverse proxy, the real client IP
        # arrives in X-Forwarded-For (uvicorn --proxy-headers sets request.client).
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Health checks and preflight requests are never throttled.
        if request.url.path in ("/health", "/docs", "/openapi.json") or request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path.startswith(self.auth_paths):
            limiter = self._limiter("auth", settings.rate_limit_auth_per_minute)
        else:
            limiter = self._limiter("general", settings.rate_limit_per_minute)
        allowed, retry_after = limiter.allowed(self._client_ip(request))
        if not allowed:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Please slow down and retry."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
