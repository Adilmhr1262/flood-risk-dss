"""Tests for the Phase W3 authority command center.

Covers the incident workflow (detected -> verified -> response_started ->
resolved), incident notes, shelter monitoring, response teams, the weather
endpoint, report priority triage, and authority-only access control. All
endpoints here require the authority role.
"""

from datetime import datetime, timezone

import pytest
from geoalchemy2 import WKTElement

from app.models import CitizenReport, Shelter, WeatherObservation

from .conftest import auth_headers, make_district, make_shelter, make_user


@pytest.fixture()
def authority(client, db):
    user = make_user(db, role="authority")
    return auth_headers(client, user)


@pytest.fixture()
def public_headers(client, db):
    user = make_user(db, role="public")
    return auth_headers(client, user)


@pytest.fixture()
def dadu(db):
    return make_district(db, name="Dadu")


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


def test_incident_full_workflow(client, db, authority, dadu):
    # Create
    res = client.post(
        "/api/v1/incidents",
        json={"title": "Embankment breach near Mehar", "district_name": "Dadu", "severity": 4},
        headers=authority,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "detected"
    assert body["district_name"] == "Dadu"
    incident_id = body["id"]

    # Invalid jump: detected -> resolved
    res = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "resolved"},
        headers=authority,
    )
    assert res.status_code == 422

    # detected -> verified (with note)
    res = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "verified", "note": "Confirmed by field team."},
        headers=authority,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "verified"
    assert len(res.json()["notes"]) == 1

    # verified -> response_started
    res = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "response_started"},
        headers=authority,
    )
    assert res.json()["status"] == "response_started"

    # response_started -> resolved
    res = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "resolved"},
        headers=authority,
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "resolved"
    assert res.json()["resolved_at"] is not None

    # Terminal state: no further transitions
    res = client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "verified"},
        headers=authority,
    )
    assert res.status_code == 422


def test_incident_notes(client, db, authority, dadu):
    res = client.post(
        "/api/v1/incidents",
        json={"title": "Test incident", "district_name": "Dadu"},
        headers=authority,
    )
    incident_id = res.json()["id"]
    res = client.post(
        f"/api/v1/incidents/{incident_id}/notes",
        json={"note": "Boat team dispatched."},
        headers=authority,
    )
    assert res.status_code == 201, res.text
    res = client.get(f"/api/v1/incidents/{incident_id}", headers=authority)
    assert any(n["note"] == "Boat team dispatched." for n in res.json()["notes"])


def test_incident_list_filter_and_stats(client, db, authority, dadu):
    for title in ("A", "B"):
        client.post("/api/v1/incidents", json={"title": title, "district_name": "Dadu"}, headers=authority)
    res = client.get("/api/v1/incidents?status=detected", headers=authority)
    assert res.status_code == 200 and len(res.json()) == 2
    res = client.get("/api/v1/incidents?status=resolved", headers=authority)
    assert res.json() == []
    res = client.get("/api/v1/incidents/stats", headers=authority)
    stats = res.json()
    assert stats["by_status"]["detected"] == 2
    assert stats["open_by_severity"]["3"] == 2


def test_incident_map_layer(client, db, authority, dadu):
    client.post(
        "/api/v1/incidents",
        json={"title": "Map incident", "district_name": "Dadu", "latitude": 26.73, "longitude": 67.78},
        headers=authority,
    )
    res = client.get("/api/v1/incidents/map", headers=authority)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    assert body["features"][0]["properties"]["status"] == "detected"


def test_incidents_require_authority(client, db, public_headers, dadu):
    assert client.get("/api/v1/incidents", headers=public_headers).status_code == 403
    assert client.post("/api/v1/incidents", json={"title": "x"}, headers=public_headers).status_code == 403
    assert client.get("/api/v1/incidents/stats", headers=public_headers).status_code == 403


def test_incident_unknown_district(client, db, authority):
    res = client.post(
        "/api/v1/incidents",
        json={"title": "Nowhere", "district_name": "Atlantis"},
        headers=authority,
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Resources: shelters and teams
# ---------------------------------------------------------------------------


def test_shelter_monitoring_update(client, db, authority, dadu):
    shelter = make_shelter(db, dadu)
    res = client.get("/api/v1/resources/shelters", headers=authority)
    assert res.status_code == 200, res.text
    row = next(r for r in res.json() if r["id"] == str(shelter.id))
    assert row["capacity"] == 500
    assert row["current_occupancy"] == 0
    assert row["availability"] == 500
    assert row["occupancy_pct"] == 0.0
    assert row["status"] == "open"

    res = client.patch(
        f"/api/v1/resources/shelters/{shelter.id}",
        json={"current_occupancy": 250},
        headers=authority,
    )
    assert res.status_code == 200, res.text
    assert res.json()["current_occupancy"] == 250
    assert res.json()["availability"] == 250
    assert res.json()["occupancy_pct"] == 50.0

    # Occupancy beyond capacity is rejected
    res = client.patch(
        f"/api/v1/resources/shelters/{shelter.id}",
        json={"current_occupancy": 600},
        headers=authority,
    )
    assert res.status_code == 422

    # Full occupancy flips status to full
    res = client.patch(
        f"/api/v1/resources/shelters/{shelter.id}",
        json={"current_occupancy": 500},
        headers=authority,
    )
    assert res.json()["status"] == "full"


def test_response_team_crud(client, db, authority, dadu):
    res = client.post(
        "/api/v1/resources/teams",
        json={"name": "Dadu Boat Team 1", "team_type": "boat", "district_name": "Dadu",
              "members_count": 8, "contact_phone": "+92-300-1111111"},
        headers=authority,
    )
    assert res.status_code == 201, res.text
    team_id = res.json()["id"]
    assert res.json()["status"] == "available"
    assert res.json()["district_name"] == "Dadu"

    res = client.patch(
        f"/api/v1/resources/teams/{team_id}", json={"status": "deployed"}, headers=authority
    )
    assert res.json()["status"] == "deployed"

    res = client.get("/api/v1/resources/teams?status=deployed", headers=authority)
    assert any(t["id"] == team_id for t in res.json())

    res = client.delete(f"/api/v1/resources/teams/{team_id}", headers=authority)
    assert res.status_code == 204
    res = client.get("/api/v1/resources/teams", headers=authority)
    assert all(t["id"] != team_id for t in res.json())


def test_resources_require_authority(client, db, public_headers):
    assert client.get("/api/v1/resources/shelters", headers=public_headers).status_code == 403
    assert client.get("/api/v1/resources/teams", headers=public_headers).status_code == 403
    assert client.get("/api/v1/resources/infrastructure", headers=public_headers).status_code == 403


# ---------------------------------------------------------------------------
# Weather, reports map, report priority
# ---------------------------------------------------------------------------


def test_weather_latest(client, db, authority, dadu):
    db.add(
        WeatherObservation(
            geographic_id=dadu.id,
            observed_at=datetime(2026, 9, 26, 6, 0, tzinfo=timezone.utc),
            rainfall_mm=12.5,
            temperature_c=31.0,
            humidity_pct=70.0,
            source="open-meteo",
        )
    )
    db.commit()
    res = client.get("/api/v1/weather/latest", headers=authority)
    assert res.status_code == 200, res.text
    row = next(r for r in res.json() if r["district_name"] == "Dadu")
    assert row["rainfall_mm"] == 12.5
    assert row["temperature_c"] == 31.0


def test_weather_requires_authority(client, db, public_headers):
    assert client.get("/api/v1/weather/latest", headers=public_headers).status_code == 403


def test_report_priority_and_map(client, db, authority, dadu):
    report = CitizenReport(
        geographic_id=dadu.id,
        geom=WKTElement("POINT(67.78 26.73)", srid=4326),
        severity=4,
        description="Water rising near the embankment",
        category="flood_water",
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    res = client.patch(
        f"/api/v1/admin/reports/{report.id}/verify",
        json={"status": "verified", "note": "Confirmed", "priority": "urgent"},
        headers=authority,
    )
    assert res.status_code == 200, res.text
    assert res.json()["priority"] == "urgent"
    assert res.json()["status"] == "verified"

    res = client.patch(
        f"/api/v1/admin/reports/{report.id}/verify",
        json={"status": "verified", "priority": "critical"},
        headers=authority,
    )
    assert res.status_code == 422

    res = client.get("/api/v1/admin/reports/map", headers=authority)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["type"] == "FeatureCollection"
    assert any(f["properties"]["priority"] == "urgent" for f in body["features"])
