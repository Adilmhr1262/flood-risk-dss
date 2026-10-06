"""Shared pytest fixtures: isolated test database + authenticated TestClient.

The test database (settings.test_database_url) is rebuilt from
database/schema.sql once per session; every test truncates all tables first
so tests are fully independent. Passwords use real bcrypt hashes.
"""

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from geoalchemy2 import WKTElement
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.deps import get_db
from app.core.security import hash_password
from app.main import app
from app.models import EmergencyContact, FloodEvent, GeographicData, Shelter, User

TEST_PASSWORD = "test-password-123"

test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

TABLES = [
    "predictions",
    "flood_events",
    "alerts",
    "shelters",
    "emergency_contacts",
    "citizen_reports",
    "device_tokens",
    "weather_observations",
    "district_boundaries",
    "incident_notes",
    "incidents",
    "response_teams",
    "users",
    "geographic_data",
]


@pytest.fixture(scope="session", autouse=True)
def _build_test_schema():
    """Rebuild the test database schema once per session via psql.

    Drops only this project's objects (never the whole schema) so the
    pre-installed postgis extension survives — flood_dss is not a superuser.
    """
    import subprocess

    schema_sql = Path(__file__).resolve().parents[2] / "database" / "schema.sql"
    # psql/libpq does not understand SQLAlchemy's +psycopg2 dialect marker.
    dsn = settings.test_database_url.replace("postgresql+psycopg2://", "postgresql://")
    subprocess.run(
        ["psql", dsn, "-v", "ON_ERROR_STOP=1", "-c",
         "DROP TABLE IF EXISTS predictions, flood_events, alerts, shelters, "
         "emergency_contacts, citizen_reports, device_tokens, weather_observations, "
         "district_boundaries, incident_notes, incidents, response_teams, users, "
         "geographic_data CASCADE; "
         "DROP TYPE IF EXISTS user_role; "
         "DROP FUNCTION IF EXISTS set_updated_at() CASCADE;"],
        check=True, capture_output=True, text=True,
    )
    result = subprocess.run(
        ["psql", dsn, "-v", "ON_ERROR_STOP=1", "-f", str(schema_sql)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"schema.sql failed:\n{result.stderr}"
    yield


@pytest.fixture(scope="session", autouse=True)
def _disable_rate_limits_for_tests():
    """The full suite issues far more requests per minute than the
    production rate limiter allows. Raise the budgets for the test session
    only — production keeps the configured limits (verified by
    test_production_hardening.py, which sets its own budgets)."""
    settings.rate_limit_per_minute = 100000
    settings.rate_limit_auth_per_minute = 100000
    yield
    settings.rate_limit_per_minute = 120
    settings.rate_limit_auth_per_minute = 20


@pytest.fixture()
def db(_build_test_schema):
    """Fresh database session with all tables truncated."""
    with test_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(TABLES)} CASCADE"))
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """FastAPI TestClient with get_db overridden to the test session."""

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(db, role="public", email=None, password=TEST_PASSWORD, name="Test User"):
    email = email or f"{role}.{uuid.uuid4().hex[:8]}@test.pk"
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        location_name="Dadu, Sindh",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(client, user, password=TEST_PASSWORD):
    res = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_district(db, name="Dadu"):
    district = GeographicData(
        district_name=name,
        province="Sindh",
        geom=WKTElement(f"POINT(67.78 26.73)", srid=4326),
        latitude=26.73,
        longitude=67.78,
        elevation_m=42.0,
        river_distance_km=3.2,
        slope_deg=1.5,
        population_density_per_km2=210.0,
        vulnerability_index=0.8,
    )
    db.add(district)
    db.commit()
    db.refresh(district)
    return district


def make_shelter(db, district):
    shelter = Shelter(
        name="Test Relief Camp",
        geographic_id=district.id,
        geom=WKTElement("POINT(67.79 26.74)", srid=4326),
        capacity=500,
        facilities=["Drinking water", "Medical tent"],
        contact_phone="+92-300-0000000",
    )
    db.add(shelter)
    db.commit()
    db.refresh(shelter)
    return shelter


def make_event(db, district):
    from datetime import date

    event = FloodEvent(
        geographic_id=district.id,
        event_date=date(2022, 8, 20),
        rainfall_mm=320.0,
        temperature_c=33.0,
        humidity_pct=85.0,
        severity=5,
        flood_status=True,
        damage_description="Test damage",
        affected_population=10000,
        source="test",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def make_contact(db, district_name="Dadu"):
    contact = EmergencyContact(
        name="Test Rescue",
        organization="Rescue 1122",
        phone="+92-21-0000000",
        district_name=district_name,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact
