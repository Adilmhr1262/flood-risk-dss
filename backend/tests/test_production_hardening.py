"""Phase W4 production-hardening tests: rate limiting, CORS config,
production secret guard, and the service status endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import _check_production_secrets, _cors_options, create_app
from app.middleware.rate_limit import RateLimitMiddleware, _SlidingWindow


def test_sliding_window_allows_then_blocks():
    w = _SlidingWindow(limit=3, window_seconds=60)
    assert w.allowed("k")[0]
    assert w.allowed("k")[0]
    assert w.allowed("k")[0]
    ok, retry_after = w.allowed("k")
    assert not ok
    assert retry_after >= 1


def test_cors_options_wildcard_disables_credentials():
    original = settings.cors_origins
    try:
        settings.cors_origins = "*"
        opts = _cors_options()
        assert opts["allow_origins"] == ["*"]
        assert opts["allow_credentials"] is False
    finally:
        settings.cors_origins = original


def test_cors_options_explicit_list_allows_credentials():
    original = settings.cors_origins
    try:
        settings.cors_origins = "https://floodsafe.example.pk, https://www.floodsafe.example.pk"
        opts = _cors_options()
        assert opts["allow_origins"] == [
            "https://floodsafe.example.pk",
            "https://www.floodsafe.example.pk",
        ]
        assert opts["allow_credentials"] is True
    finally:
        settings.cors_origins = original


def test_production_secret_guard_rejects_placeholders(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "secret_key", "change-me-to-a-long-random-secret")
    monkeypatch.setattr(settings, "cors_origins", "*")
    with pytest.raises(RuntimeError, match="Production safety checks failed"):
        _check_production_secrets()


def test_production_secret_guard_passes_with_real_values(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "secret_key", "a-real-secret-value-from-env")
    monkeypatch.setattr(settings, "cors_origins", "https://floodsafe.example.pk")
    _check_production_secrets()  # must not raise


def test_create_app_registers_rate_limit_middleware():
    app = create_app()
    middleware_names = [m.cls.__name__ for m in app.user_middleware]
    assert "RateLimitMiddleware" in middleware_names


def test_health_endpoint_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_status_endpoint_reports_database(client):
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"]["ok"] is True
    assert body["status"] in ("ok", "degraded")
    assert "model" in body and "scheduler" in body


def test_rate_limiter_blocks_auth_flood(client, monkeypatch):
    # Shrink the auth budget so the test runs fast.
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 3)
    flood_app = create_app()
    flood_client = TestClient(flood_app)
    statuses = set()
    for _ in range(6):
        r = flood_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )
        statuses.add(r.status_code)
    assert 429 in statuses
    # The 429 response carries a Retry-After hint.
    r = flood_client.post("/api/v1/auth/login", json={"email": "x@y.z", "password": "w"})
    if r.status_code == 429:
        assert "retry-after" in {k.lower() for k in r.headers}
