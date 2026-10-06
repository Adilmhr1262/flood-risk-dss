"""Tests for Phase 4 GIS intelligence layers and decision support API."""

from datetime import date

import pytest
from geoalchemy2 import WKTElement
from sqlalchemy import inspect, text

from app.models import (
    Alert,
    FloodEvent,
    GeographicData,
    Infrastructure,
    Prediction,
    ResourceAllocation,
    Shelter,
    VulnerabilityIndicator,
)
from tests.conftest import auth_headers, make_district, make_user

NEW_TABLES = ["infrastructure", "vulnerability_indicators", "resource_allocations"]


@pytest.fixture()
def ds_data(db):
    """Districts + predictions + vulnerability + infrastructure + alerts."""
    # Fresh truncate for the Phase 4 tables (conftest's TABLES list predates them).
    with db.bind.begin() as conn:
        conn.execute(text("TRUNCATE infrastructure, vulnerability_indicators, resource_allocations"))
    dadu = make_district(db, "Dadu")
    larkana = make_district(db, "Larkana")

    db.add(
        Prediction(
            geographic_id=dadu.id,
            model_version="mlp-v1",
            probability=0.91,
            risk_level="HIGH",
            input_features={"district_name": "Dadu", "rainfall_mm": 300.0},
            main_factors=["Heavy rainfall", "Low elevation"],
            recommendations=["Prepare evacuation plans"],
        )
    )
    db.add(
        Prediction(
            geographic_id=larkana.id,
            model_version="mlp-v1",
            probability=0.20,
            risk_level="LOW",
            input_features={"district_name": "Larkana", "rainfall_mm": 40.0},
            main_factors=["Normal conditions"],
            recommendations=["Continue routine monitoring"],
        )
    )
    db.add(
        VulnerabilityIndicator(
            geographic_id=dadu.id,
            population_density=268.0,
            vulnerability_index=0.3315,
            notes="test seed",
        )
    )
    db.add(
        VulnerabilityIndicator(
            geographic_id=larkana.id,
            population_density=420.0,
            vulnerability_index=0.2745,
            notes="test seed",
        )
    )
    db.add(
        Infrastructure(
            name="Dadu Civil Hospital",
            type="hospital",
            geographic_id=dadu.id,
            geom=WKTElement("POINT(67.79 26.75)", srid=4326),
            capacity=200,
            operational_status="operational",
            is_sample_data=True,
        )
    )
    db.add(
        Infrastructure(
            name="Rescue 1122 Station Dadu",
            type="rescue_center",
            geographic_id=dadu.id,
            geom=WKTElement("POINT(67.76 26.72)", srid=4326),
            capacity=40,
            operational_status="operational",
            is_sample_data=True,
        )
    )
    db.add(
        Shelter(
            name="Dadu Relief Camp",
            geographic_id=dadu.id,
            geom=WKTElement("POINT(67.80 26.74)", srid=4326),
            capacity=1200,
            facilities=["Drinking water"],
            contact_phone="+92-300-1111111",
        )
    )
    db.add(
        Alert(
            geographic_id=dadu.id,
            title="Flash flood warning",
            message="Heavy rainfall detected",
            severity="warning",
            is_active=True,
        )
    )
    db.add(
        FloodEvent(
            geographic_id=dadu.id,
            event_date=date(2022, 8, 26),
            rainfall_mm=398.0,
            severity=5,
            flood_status=True,
            affected_population=18000,
            source="test",
        )
    )
    db.commit()
    return {"dadu": dadu, "larkana": larkana}


def _geojson_ok(data):
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)
    for f in data["features"]:
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] in ("Point", "MultiPolygon", "Polygon")
        assert isinstance(f["geometry"]["coordinates"], list)


def test_new_tables_exist(db):
    names = inspect(db.bind).get_table_names()
    for t in NEW_TABLES:
        assert t in names, f"missing table {t}"


def test_vulnerability_map_geojson(client, db, ds_data):
    user = make_user(db, role="authority")
    res = client.get("/api/v1/gis/vulnerability-map", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    data = res.json()
    _geojson_ok(data)
    dadu = next(f for f in data["features"] if f["properties"]["district_name"] == "Dadu")
    props = dadu["properties"]
    assert props["vulnerability_index"] == pytest.approx(0.3315)
    assert props["population_density"] == pytest.approx(268.0)
    assert props["risk_level"] == "HIGH"
    assert props["priority"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def test_infrastructure_filtering(client, db, ds_data):
    user = make_user(db, role="authority")
    headers = auth_headers(client, user)
    res = client.get("/api/v1/gis/infrastructure", headers=headers)
    assert res.status_code == 200
    _geojson_ok(res.json())
    assert len(res.json()["features"]) == 2

    res = client.get("/api/v1/gis/infrastructure?type=hospital", headers=headers)
    assert res.status_code == 200
    feats = res.json()["features"]
    assert len(feats) == 1
    assert feats[0]["properties"]["type"] == "hospital"
    assert feats[0]["properties"]["is_sample_data"] is True

    res = client.get("/api/v1/gis/infrastructure?district_name=Larkana", headers=headers)
    assert res.status_code == 200
    assert res.json()["features"] == []


def test_risk_layer_covers_all_districts(client, db, ds_data):
    user = make_user(db, role="ngo")
    res = client.get("/api/v1/gis/risk-layer", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    data = res.json()
    _geojson_ok(data)
    by_name = {f["properties"]["district_name"]: f["properties"] for f in data["features"]}
    assert by_name["Dadu"]["risk_level"] == "HIGH"
    assert by_name["Dadu"]["probability"] == pytest.approx(91.0)


def test_historical_floods_rich_properties(client, db, ds_data):
    user = make_user(db, role="authority")
    headers = auth_headers(client, user)
    res = client.get("/api/v1/gis/historical-floods", headers=headers)
    assert res.status_code == 200
    data = res.json()
    _geojson_ok(data)
    props = data["features"][0]["properties"]
    assert props["year"] == 2022
    assert props["severity"] == 5
    assert props["severity_label"] == "Catastrophic"
    assert props["affected_population"] == 18000

    res = client.get("/api/v1/gis/historical-floods?from_year=2020&to_year=2024", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["features"]) == 1
    res = client.get("/api/v1/gis/historical-floods?district_name=Larkana", headers=headers)
    assert res.status_code == 200
    assert res.json()["features"] == []


def test_decision_support_summary_shape(client, db, ds_data):
    user = make_user(db, role="authority")
    res = client.get("/api/v1/decision-support/summary", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    data = res.json()
    for key in ("high_risk_districts", "active_alerts", "latest_predictions",
                "resource_overview", "vulnerability_hotspots"):
        assert key in data, f"missing {key}"

    assert len(data["high_risk_districts"]) == 1
    hr = data["high_risk_districts"][0]
    assert hr["district_name"] == "Dadu"
    assert hr["probability"] == pytest.approx(0.91)
    assert hr["risk_level"] == "HIGH"
    assert isinstance(hr["top_factors"], list) and len(hr["top_factors"]) > 0
    assert isinstance(hr["recommended_actions"], list) and len(hr["recommended_actions"]) > 0

    assert len(data["active_alerts"]) == 1
    assert data["active_alerts"][0]["district_name"] == "Dadu"

    assert len(data["latest_predictions"]) == 2
    ro = data["resource_overview"]
    assert ro["shelters"]["count"] == 1
    assert ro["shelters"]["total_capacity"] == 1200
    assert ro["infrastructure_by_type"]["hospital"] == 1
    assert ro["infrastructure_by_type"]["rescue_center"] == 1

    # authority sees allocations list; ngo does not
    assert "allocations" in data
    ngo = make_user(db, role="ngo")
    res2 = client.get("/api/v1/decision-support/summary", headers=auth_headers(client, ngo))
    assert res2.status_code == 200
    assert "allocations" not in res2.json()


def test_decision_support_trends(client, db, ds_data):
    user = make_user(db, role="authority")
    res = client.get("/api/v1/decision-support/trends", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    data = res.json()
    assert "year_wise" in data and "seasonal_pattern" in data
    dadu = next(d for d in data["year_wise"] if d["district_name"] == "Dadu")
    assert dadu["total_events"] == 1
    assert dadu["yearly"][0]["year"] == 2022
    assert "trend_2017_2024_vs_2010_2016" in dadu
    august = next(m for m in data["seasonal_pattern"] if m["month"] == 8)
    assert august["events"] == 1


def test_decision_support_auth_guards(client, db, ds_data):
    # unauthenticated -> 401
    res = client.get("/api/v1/decision-support/summary")
    assert res.status_code == 401
    # public role blocked (staff only)
    public = make_user(db, role="public")
    res = client.get("/api/v1/decision-support/summary", headers=auth_headers(client, public))
    assert res.status_code == 403
    res = client.get("/api/v1/gis/vulnerability-map")
    assert res.status_code == 401


def test_resource_allocation_crud(client, db, ds_data):
    authority = make_user(db, role="authority")
    ngo = make_user(db, role="ngo")
    payload = {"district_name": "Dadu", "resource_type": "boats", "quantity": 12,
               "status": "planned", "notes": "test allocation"}
    res = client.post("/api/v1/decision-support/resources",
                      json=payload, headers=auth_headers(client, authority))
    assert res.status_code == 201, res.text
    assert res.json()["district_name"] == "Dadu"
    assert res.json()["quantity"] == 12

    res = client.post("/api/v1/decision-support/resources",
                      json=payload, headers=auth_headers(client, ngo))
    assert res.status_code == 403

    res = client.get("/api/v1/decision-support/resources", headers=auth_headers(client, ngo))
    assert res.status_code == 200
    assert len(res.json()) == 1

    # unknown district -> 404
    bad = dict(payload, district_name="Nowhere")
    res = client.post("/api/v1/decision-support/resources",
                      json=bad, headers=auth_headers(client, authority))
    assert res.status_code == 404
