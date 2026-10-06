"""Tests for the Phase 5 mobile API (/mobile/*) and the volunteer role."""

import pytest
from geoalchemy2 import WKTElement

from app.models import CitizenReport, Prediction, Shelter
from tests.conftest import auth_headers, make_contact, make_district, make_user


def _prediction(db, district, probability=0.82, level="HIGH"):
    db.add(
        Prediction(
            geographic_id=district.id,
            model_version="mlp-v1",
            probability=probability,
            risk_level=level,
            input_features={"district_name": district.district_name},
            main_factors=["Heavy rainfall", "Low elevation"],
            recommendations=["Prepare evacuation plans"],
        )
    )
    db.commit()


def test_register_volunteer_role(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Vol", "email": "vol@example.pk", "password": "secret123", "role": "volunteer"},
    )
    assert res.status_code == 201, res.text
    assert res.json()["role"] == "volunteer"


def test_volunteer_can_use_mobile_alerts(client, db):
    user = make_user(db, role="volunteer")
    headers = auth_headers(client, user)
    res = client.get("/api/v1/mobile/alerts", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_mobile_requires_auth(client):
    res = client.get("/api/v1/mobile/alerts")
    assert res.status_code == 401


def test_my_risk_returns_latest_prediction(client, db):
    district = make_district(db, "Dadu")
    _prediction(db, district, probability=0.82, level="HIGH")
    user = make_user(db, role="public")
    res = client.get("/api/v1/mobile/my-risk?district_name=Dadu", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["district_name"] == "Dadu"
    assert body["risk_level"] == "HIGH"
    assert body["probability"] == 82.0
    assert body["main_factors"] == ["Heavy rainfall", "Low elevation"]
    assert body["recommendations"] == ["Prepare evacuation plans"]
    assert body["model_version"] == "mlp-v1"
    assert body["updated_at"] is not None


def test_my_risk_no_prediction_yet(client, db):
    make_district(db, "Dadu")
    user = make_user(db, role="public")
    res = client.get("/api/v1/mobile/my-risk?district_name=Dadu", headers=auth_headers(client, user))
    assert res.status_code == 404


def test_my_risk_gps_match(client, db):
    district = make_district(db, "Dadu")  # centroid 26.73, 67.78
    _prediction(db, district)
    user = make_user(db, role="public")
    res = client.get(
        "/api/v1/mobile/my-risk?lat=26.75&lon=67.80", headers=auth_headers(client, user)
    )
    assert res.status_code == 200, res.text
    assert res.json()["district_name"] == "Dadu"


def test_my_risk_unknown_district(client, db):
    user = make_user(db, role="public")
    res = client.get("/api/v1/mobile/my-risk?district_name=Nowhere", headers=auth_headers(client, user))
    assert res.status_code == 404


def test_shelters_nearby_ordering_and_radius(client, db):
    district = make_district(db, "Dadu")
    near = Shelter(
        name="Near Camp",
        geographic_id=district.id,
        geom=WKTElement("POINT(67.79 26.74)", srid=4326),
        capacity=200,
    )
    far = Shelter(
        name="Far Camp",
        geographic_id=district.id,
        geom=WKTElement("POINT(68.50 27.50)", srid=4326),  # ~110 km away
        capacity=300,
    )
    db.add_all([near, far])
    db.commit()
    user = make_user(db, role="volunteer")
    headers = auth_headers(client, user)

    res = client.get(
        "/api/v1/mobile/shelters/nearby?lat=26.73&lon=67.78&radius_km=500",
        headers=headers,
    )
    assert res.status_code == 200, res.text
    items = res.json()
    assert len(items) == 2
    assert items[0]["name"] == "Near Camp"
    assert items[0]["distance_km"] < items[1]["distance_km"]
    assert items[0]["capacity"] == 200

    res = client.get(
        "/api/v1/mobile/shelters/nearby?lat=26.73&lon=67.78&radius_km=20",
        headers=headers,
    )
    assert res.status_code == 200
    assert [i["name"] for i in res.json()] == ["Near Camp"]


def test_report_event_creates_pending_report(client, db):
    make_district(db, "Dadu")
    user = make_user(db, role="volunteer")
    res = client.post(
        "/api/v1/mobile/report-event",
        headers=auth_headers(client, user),
        json={
            "district_name": "Dadu",
            "lat": 26.74,
            "lon": 67.79,
            "severity": 4,
            "description": "Water rising near the river bank",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "pending"
    assert body["severity"] == 4
    assert body["district_name"] == "Dadu"

    row = db.query(CitizenReport).filter(CitizenReport.id == body["id"]).first()
    assert row is not None
    assert row.reporter_id == user.id


def test_report_event_validation(client, db):
    make_district(db, "Dadu")
    user = make_user(db, role="public")
    headers = auth_headers(client, user)
    # severity out of range -> 422
    res = client.post(
        "/api/v1/mobile/report-event",
        headers=headers,
        json={"district_name": "Dadu", "lat": 26.7, "lon": 67.8, "severity": 9},
    )
    assert res.status_code == 422
    # unknown district -> 404
    res = client.post(
        "/api/v1/mobile/report-event",
        headers=headers,
        json={"district_name": "Nowhere", "lat": 26.7, "lon": 67.8, "severity": 3},
    )
    assert res.status_code == 404


def test_report_event_authority_forbidden(client, db):
    make_district(db, "Dadu")
    user = make_user(db, role="authority")
    res = client.post(
        "/api/v1/mobile/report-event",
        headers=auth_headers(client, user),
        json={"district_name": "Dadu", "lat": 26.7, "lon": 67.8, "severity": 3},
    )
    assert res.status_code == 403


def test_my_reports_lists_own_reports(client, db):
    make_district(db, "Dadu")
    user = make_user(db, role="volunteer")
    headers = auth_headers(client, user)
    client.post(
        "/api/v1/mobile/report-event",
        headers=headers,
        json={"district_name": "Dadu", "lat": 26.7, "lon": 67.8, "severity": 2, "description": "x"},
    )
    other = make_user(db, role="public", email="other@example.pk")
    client.post(
        "/api/v1/mobile/report-event",
        headers=auth_headers(client, other),
        json={"district_name": "Dadu", "lat": 26.7, "lon": 67.8, "severity": 3},
    )
    res = client.get("/api/v1/mobile/reports/mine", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["severity"] == 2


def test_emergency_contacts_filter(client, db):
    make_contact(db, district_name="Dadu")
    make_contact(db, district_name="Larkana")
    user = make_user(db, role="public")
    res = client.get(
        "/api/v1/mobile/emergency-contacts?district_name=Dadu",
        headers=auth_headers(client, user),
    )
    assert res.status_code == 200
    assert all(c["district_name"] == "Dadu" for c in res.json())
    assert len(res.json()) >= 1
