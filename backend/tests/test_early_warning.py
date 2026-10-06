"""Tests for Phase 6 early warning automation.

Covers the alert rule table, cooldown/escalation logic, device token
endpoints, citizen report categories + image upload + verification workflow,
and the admin triage queue. Weather fetching itself is not hit over the
network here — _district_weather_features reads weather_observations rows
inserted directly, and run_early_warning_cycle is exercised end to end.
"""

from datetime import datetime, timedelta, timezone

from app.models import Alert, CitizenReport, DeviceToken, WeatherObservation
from app.services import alert_engine
from app.services.alert_engine import decide, run_early_warning_cycle
from tests.conftest import TEST_PASSWORD, auth_headers, make_district, make_user

HIGH_ASSESSMENT = {
    "risk_level": "HIGH",
    "probability": 0.92,
    "main_factors": ["Heavy rainfall", "River proximity"],
    "recommendations": ["Prepare evacuation plans"],
    "model_version": "rule-based-v1",
}
MEDIUM_ASSESSMENT = {
    "risk_level": "MEDIUM",
    "probability": 0.45,
    "main_factors": ["Moderate rainfall"],
    "recommendations": ["Monitor weather forecasts"],
    "model_version": "rule-based-v1",
}
LOW_ASSESSMENT = {
    "risk_level": "LOW",
    "probability": 0.08,
    "main_factors": [],
    "recommendations": [],
    "model_version": "rule-based-v1",
}


def _forecast_rain(db, district, mm: float):
    """Insert a forecast observation row the alert engine will pick up."""
    db.add(
        WeatherObservation(
            geographic_id=district.id,
            observed_at=datetime.now(timezone.utc) + timedelta(hours=2),
            rainfall_mm=mm,
            temperature_c=34.0,
            humidity_pct=85.0,
            source="open-meteo",
        )
    )
    db.commit()


# --- alert rule table -------------------------------------------------------


def test_decide_low_issues_no_alert():
    assert decide("Dadu", LOW_ASSESSMENT) is None


def test_decide_medium_is_advisory():
    d = decide("Dadu", MEDIUM_ASSESSMENT)
    assert d["severity"] == "watch"
    assert "advisory" in d["title"].lower()


def test_decide_high_is_emergency():
    d = decide("Dadu", HIGH_ASSESSMENT)
    assert d["severity"] == "emergency"
    assert "Dadu" in d["title"]


# --- cooldown / escalation --------------------------------------------------


def test_cooldown_suppresses_repeat_alert(db):
    district = make_district(db)
    _forecast_rain(db, district, 500.0)
    before = db.query(Alert).count()
    out1 = run_early_warning_cycle(
        db, model_name="rule-based-v1", district_names=["Dadu"], notify=lambda p: None
    )
    assert out1["alerts_issued"] == 1
    out2 = run_early_warning_cycle(
        db, model_name="rule-based-v1", district_names=["Dadu"], notify=lambda p: None
    )
    assert out2["alerts_issued"] == 0
    assert "cooldown" in out2["outcomes"][0].get("skipped", "")
    assert db.query(Alert).count() == before + 1


def test_escalation_issues_immediately(db):
    district = make_district(db)
    old = Alert(
        geographic_id=district.id,
        title="Flood advisory: Dadu",
        message="advisory",
        severity="watch",
    )
    db.add(old)
    db.commit()
    _forecast_rain(db, district, 500.0)
    out = run_early_warning_cycle(
        db, model_name="rule-based-v1", district_names=["Dadu"], notify=lambda p: None
    )
    assert out["alerts_issued"] == 1
    assert out["outcomes"][0].get("escalated_from") == "MEDIUM"
    db.refresh(old)
    assert old.is_active is False


def test_cycle_stores_provenance(db):
    district = make_district(db)
    _forecast_rain(db, district, 500.0)
    run_early_warning_cycle(
        db, model_name="rule-based-v1", district_names=["Dadu"], notify=lambda p: None
    )
    alert = db.query(Alert).order_by(Alert.issued_at.desc()).first()
    assert alert.severity == "emergency"
    assert alert.model_version == "rule-based-v1"
    assert alert.probability and alert.probability > 0.66
    assert isinstance(alert.factors, list) and alert.factors


def test_cycle_low_weather_issues_nothing(db):
    # A low-vulnerability district with a dry forecast scores LOW -> no alert.
    from geoalchemy2 import WKTElement

    from app.models import GeographicData

    district = GeographicData(
        district_name="SafeDistrict",
        province="Sindh",
        geom=WKTElement("POINT(68.5 27.0)", srid=4326),
        latitude=27.0,
        longitude=68.5,
        elevation_m=300.0,
        river_distance_km=80.0,
        vulnerability_index=0.1,
        population_density_per_km2=20.0,
    )
    db.add(district)
    db.commit()
    _forecast_rain(db, district, 2.0)
    out = run_early_warning_cycle(
        db,
        model_name="rule-based-v1",
        district_names=["SafeDistrict"],
        notify=lambda p: None,
    )
    assert out["alerts_issued"] == 0
    assert out["outcomes"][0]["risk_level"] == "LOW"


# --- device tokens ----------------------------------------------------------


def test_device_token_register_and_delete(client, db):
    user = make_user(db, role="public")
    headers = auth_headers(client, user)
    r = client.post(
        "/api/v1/mobile/device-token",
        json={"fcm_token": "test-fcm-token-abcdef123456", "platform": "android"},
        headers=headers,
    )
    assert r.status_code == 201
    assert db.query(DeviceToken).count() == 1
    # Re-registering the same token updates instead of duplicating.
    r2 = client.post(
        "/api/v1/mobile/device-token",
        json={"fcm_token": "test-fcm-token-abcdef123456", "platform": "ios"},
        headers=headers,
    )
    assert r2.status_code == 201
    assert db.query(DeviceToken).count() == 1
    r3 = client.delete(
        "/api/v1/mobile/device-token",
        params={"fcm_token": "test-fcm-token-abcdef123456"},
        headers=headers,
    )
    assert r3.status_code == 204
    assert db.query(DeviceToken).count() == 0


def test_device_token_requires_auth(client, db):
    r = client.post("/api/v1/mobile/device-token", json={"fcm_token": "x" * 20})
    assert r.status_code == 401


# --- citizen report categories / images / verification ----------------------


def test_report_with_category(client, db):
    user = make_user(db, role="volunteer")
    make_district(db)
    headers = auth_headers(client, user)
    r = client.post(
        "/api/v1/mobile/report-event",
        json={
            "district_name": "Dadu",
            "lat": 26.73,
            "lon": 67.78,
            "severity": 4,
            "description": "Water over the road",
            "category": "road_blockage",
        },
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["category"] == "road_blockage"
    assert r.json()["status"] == "pending"


def test_report_bad_category_rejected(client, db):
    user = make_user(db, role="public")
    make_district(db)
    headers = auth_headers(client, user)
    r = client.post(
        "/api/v1/mobile/report-event",
        json={
            "district_name": "Dadu",
            "lat": 26.73,
            "lon": 67.78,
            "severity": 3,
            "category": "alien_invasion",
        },
        headers=headers,
    )
    assert r.status_code == 422


def test_report_image_upload(client, db):
    user = make_user(db, role="volunteer")
    make_district(db)
    headers = auth_headers(client, user)
    r = client.post(
        "/api/v1/mobile/report-event",
        json={"district_name": "Dadu", "lat": 26.73, "lon": 67.78, "severity": 3},
        headers=headers,
    )
    report_id = r.json()["id"]
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # minimal fake PNG
    r2 = client.post(
        f"/api/v1/mobile/report-event/{report_id}/image",
        files={"file": ("photo.png", png, "image/png")},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["image_path"].endswith(".png")
    # Wrong extension rejected.
    r3 = client.post(
        f"/api/v1/mobile/report-event/{report_id}/image",
        files={"file": ("evil.exe", b"data", "application/octet-stream")},
        headers=headers,
    )
    assert r3.status_code == 422


def test_report_image_forbidden_for_stranger(client, db):
    reporter = make_user(db, role="volunteer")
    stranger = make_user(db, role="public")
    make_district(db)
    r = client.post(
        "/api/v1/mobile/report-event",
        json={"district_name": "Dadu", "lat": 26.73, "lon": 67.78, "severity": 3},
        headers=auth_headers(client, reporter),
    )
    report_id = r.json()["id"]
    r2 = client.post(
        f"/api/v1/mobile/report-event/{report_id}/image",
        files={"file": ("p.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        headers=auth_headers(client, stranger),
    )
    assert r2.status_code == 403


def test_admin_report_triage_workflow(client, db):
    authority = make_user(db, role="authority")
    volunteer = make_user(db, role="volunteer")
    public = make_user(db, role="public")
    make_district(db)
    r = client.post(
        "/api/v1/mobile/report-event",
        json={
            "district_name": "Dadu",
            "lat": 26.73,
            "lon": 67.78,
            "severity": 5,
            "category": "rescue_request",
        },
        headers=auth_headers(client, volunteer),
    )
    report_id = r.json()["id"]
    auth_h = auth_headers(client, authority)

    # Queue visible to authority, filtered by status.
    q = client.get("/api/v1/admin/reports", params={"status": "pending"}, headers=auth_h)
    assert q.status_code == 200
    assert any(row["id"] == report_id for row in q.json())

    # Public users cannot see the triage queue.
    q2 = client.get(
        "/api/v1/admin/reports", headers=auth_headers(client, public)
    )
    assert q2.status_code == 403

    # Verify the report.
    v = client.patch(
        f"/api/v1/admin/reports/{report_id}/verify",
        json={"status": "verified", "note": "Confirmed by field team"},
        headers=auth_h,
    )
    assert v.status_code == 200
    body = v.json()
    assert body["status"] == "verified"
    assert body["verified_by"] == str(authority.id)
    assert body["verified_at"] is not None
    assert body["verification_note"] == "Confirmed by field team"

    # Invalid transition rejected.
    v2 = client.patch(
        f"/api/v1/admin/reports/{report_id}/verify",
        json={"status": "maybe"},
        headers=auth_h,
    )
    assert v2.status_code == 422
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    assert report.status == "verified"


# --- notifications degraded mode --------------------------------------------


def test_notifications_degraded_without_credentials():
    from app.services import notifications

    status = notifications.fcm_status()
    assert status["mode"] == "degraded"
