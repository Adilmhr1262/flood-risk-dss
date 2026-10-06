"""API integration tests against the test database: dashboard, risk, alerts."""

from datetime import date

import pytest

from .conftest import auth_headers, make_district, make_event, make_user

PREDICT_PAYLOAD = {
    "district_name": "Dadu",
    "rainfall_mm": 320.0,
    "temperature_c": 33.0,
    "humidity_pct": 82.0,
    "elevation_m": 42.0,
    "river_distance_km": 3.2,
    "slope_deg": 1.2,
    "population_density": 280.0,
    "prev_flood_events": 4,
    "last_severity": 3,
}


def test_dashboard_summary_shape(client, db):
    user = make_user(db, role="authority")
    district = make_district(db)
    make_event(db, district)
    res = client.get("/api/v1/dashboard/summary", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total_historical_events"] == 1
    assert body["active_alerts"] == 0
    assert body["high_risk_areas"] == 0
    assert body["current_risk_status"] in ("LOW", "MEDIUM", "HIGH")


def test_dashboard_summary_visible_to_public_role(client, db):
    # Dashboard aggregates are public statistics; every role may read them.
    user = make_user(db, role="public")
    res = client.get("/api/v1/dashboard/summary", headers=auth_headers(client, user))
    assert res.status_code == 200


def test_dashboard_trend_endpoints(client, db):
    user = make_user(db, role="ngo")
    district = make_district(db)
    make_event(db, district)
    headers = auth_headers(client, user)
    for path in ("/api/v1/dashboard/rainfall-trends", "/api/v1/dashboard/flood-frequency"):
        res = client.get(path, headers=headers)
        assert res.status_code == 200, res.text
        assert isinstance(res.json(), list)
    res = client.get("/api/v1/dashboard/risk-distribution", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), dict)


def test_risk_predict_persists_row(client, db):
    from app.models import Prediction

    user = make_user(db, role="public")
    make_district(db)
    headers = auth_headers(client, user)

    res = client.post("/api/v1/risk/predict", json=PREDICT_PAYLOAD, headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert body["main_factors"]
    assert body["recommendations"]
    assert body["prediction_id"] is not None

    rows = db.query(Prediction).all()
    assert len(rows) == 1
    assert rows[0].created_by == user.id
    assert rows[0].geographic.district_name == "Dadu"
    assert 0.0 <= rows[0].probability <= 1.0


def test_risk_predict_unknown_district_404(client, db):
    user = make_user(db, role="public")
    payload = dict(PREDICT_PAYLOAD, district_name="Nowhere")
    res = client.post("/api/v1/risk/predict", json=payload, headers=auth_headers(client, user))
    assert res.status_code == 404


def test_prediction_history_lists_rows(client, db):
    user = make_user(db, role="authority")
    district = make_district(db)
    make_event(db, district)
    headers = auth_headers(client, user)
    client.post("/api/v1/risk/predict", json=PREDICT_PAYLOAD, headers=headers)

    res = client.get("/api/v1/risk/predictions", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert 0.0 <= body["items"][0]["probability"] <= 1.0

    filtered = client.get("/api/v1/risk/predictions?district_name=Dadu", headers=headers)
    assert filtered.json()["total"] == 1
    filtered_none = client.get("/api/v1/risk/predictions?district_name=Larkana", headers=headers)
    assert filtered_none.json()["total"] == 0


def test_model_info_lists_registry(client, db):
    user = make_user(db, role="public")
    res = client.get("/api/v1/risk/model-info", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    body = res.json()
    assert "models" in body and "default_model" in body


def test_risk_predict_phase3_aliases(client, db):
    """The randomforest/xgboost/mlp aliases return 200, a prediction id,
    and contribution-based explanations."""
    from app.models import Prediction

    user = make_user(db, role="public")
    make_district(db)
    headers = auth_headers(client, user)
    for alias, canonical in (
        ("randomforest", "randomforest-v1"),
        ("xgboost", "xgboost-v1"),
        ("mlp", "mlp-v1"),
    ):
        payload = dict(PREDICT_PAYLOAD, vulnerability_index=0.33)
        res = client.post(
            f"/api/v1/risk/predict?model={alias}", json=payload, headers=headers
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["model_requested"] == alias
        assert body["model_version"] == canonical
        assert body["prediction_id"] is not None
        assert 0.0 <= body["probability"] <= 1.0
        assert body["main_factors"]
        contribs = body["feature_contributions"]
        assert len(contribs) == 5, alias
        total = sum(c["contribution"] for c in contribs)
        assert total == pytest.approx(1.0, abs=1e-3)
        db.query(Prediction).filter(
            Prediction.id == body["prediction_id"]
        ).delete()
        db.commit()


def test_risk_predict_legacy_rf_v1_still_works(client, db):
    user = make_user(db, role="public")
    make_district(db)
    res = client.post(
        "/api/v1/risk/predict?model=rf-v1",
        json=PREDICT_PAYLOAD,
        headers=auth_headers(client, user),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["model_version"] == "rf-v1"
    assert body["prediction_id"] is not None


def test_risk_predict_unknown_model_falls_back(client, db):
    user = make_user(db, role="public")
    make_district(db)
    res = client.post(
        "/api/v1/risk/predict?model=not-a-model",
        json=PREDICT_PAYLOAD,
        headers=auth_headers(client, user),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["note"] is not None
    assert "not-a-model" in body["note"]
    assert body["feature_contributions"] == []


def test_alerts_crud_as_authority(client, db):
    user = make_user(db, role="authority")
    district = make_district(db)
    headers = auth_headers(client, user)

    created = client.post(
        "/api/v1/alerts",
        json={
            "title": "Test warning",
            "message": "Heavy rainfall expected",
            "severity": "warning",
            "district_name": district.district_name,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    alert_id = created.json()["id"]

    listed = client.get("/api/v1/alerts", headers=headers)
    assert listed.json()["total"] == 1

    deactivated = client.patch(f"/api/v1/alerts/{alert_id}/deactivate", headers=headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    deleted = client.delete(f"/api/v1/alerts/{alert_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/v1/alerts", headers=headers).json()["total"] == 0


def test_public_cannot_create_alert(client, db):
    user = make_user(db, role="public")
    district = make_district(db)
    res = client.post(
        "/api/v1/alerts",
        json={
            "title": "x",
            "message": "y",
            "severity": "info",
            "district_name": district.district_name,
        },
        headers=auth_headers(client, user),
    )
    assert res.status_code == 403
