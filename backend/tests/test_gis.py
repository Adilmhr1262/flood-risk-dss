"""GIS layer tests: GeoJSON structure validation for all spatial endpoints."""

from sqlalchemy import inspect

from app.db.session import engine
from .conftest import (
    auth_headers,
    make_contact,
    make_district,
    make_event,
    make_shelter,
    make_user,
)

VALID_LEVELS = {"LOW", "MEDIUM", "HIGH"}


def _assert_feature_collection(body):
    assert body["type"] == "FeatureCollection"
    assert isinstance(body["features"], list)
    return body["features"]


def _assert_point_feature(feature, required_props):
    assert feature["type"] == "Feature"
    geom = feature["geometry"]
    assert geom["type"] == "Point"
    assert len(geom["coordinates"]) == 2
    lon, lat = geom["coordinates"]
    assert -180 <= lon <= 180 and -90 <= lat <= 90
    for prop in required_props:
        assert prop in feature["properties"], f"missing property: {prop}"


def _predict(client, headers, district_name="Dadu"):
    payload = {
        "district_name": district_name,
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
    res = client.post("/api/v1/risk/predict", json=payload, headers=headers)
    assert res.status_code == 200, res.text


def test_risk_layers_geojson(client, db):
    user = make_user(db, role="public")
    make_district(db)
    headers = auth_headers(client, user)
    _predict(client, headers)

    res = client.get("/api/v1/gis/risk-layers", headers=headers)
    assert res.status_code == 200, res.text
    features = _assert_feature_collection(res.json())
    assert len(features) == 1
    _assert_point_feature(
        features[0],
        ["district_name", "risk_level", "probability", "color", "model_version"],
    )
    assert features[0]["properties"]["district_name"] == "Dadu"
    assert features[0]["properties"]["risk_level"] in VALID_LEVELS


def test_risk_layers_empty_without_predictions(client, db):
    user = make_user(db, role="public")
    make_district(db)
    res = client.get("/api/v1/gis/risk-layers", headers=auth_headers(client, user))
    assert res.status_code == 200
    assert res.json()["features"] == []


def test_historical_layers_geojson(client, db):
    user = make_user(db, role="ngo")
    district = make_district(db)
    make_event(db, district)

    res = client.get("/api/v1/gis/historical-layers", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    features = _assert_feature_collection(res.json())
    assert len(features) == 1
    _assert_point_feature(
        features[0],
        ["district_name", "event_date", "severity", "rainfall_mm", "affected_population"],
    )
    assert features[0]["properties"]["event_date"].startswith("2022-08-20")


def test_shelters_geojson(client, db):
    user = make_user(db, role="public")
    district = make_district(db)
    make_shelter(db, district)

    res = client.get("/api/v1/gis/shelters", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    features = _assert_feature_collection(res.json())
    assert len(features) == 1
    _assert_point_feature(
        features[0], ["name", "district_name", "capacity", "facilities", "contact_phone"]
    )
    assert features[0]["properties"]["name"] == "Test Relief Camp"
    assert features[0]["properties"]["capacity"] == 500


def test_emergency_contacts_list_and_filter(client, db):
    user = make_user(db, role="public")
    make_contact(db, "Dadu")
    make_contact(db, "Larkana")
    headers = auth_headers(client, user)

    res = client.get("/api/v1/gis/emergency-contacts", headers=headers)
    assert res.status_code == 200, res.text
    assert len(res.json()) == 2

    filtered = client.get("/api/v1/gis/emergency-contacts?district_name=dadu", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["district_name"] == "Dadu"


def test_districts_geojson_full_attributes(client, db):
    user = make_user(db, role="ngo")
    make_district(db)

    res = client.get("/api/v1/gis/districts", headers=auth_headers(client, user))
    assert res.status_code == 200, res.text
    features = _assert_feature_collection(res.json())
    assert len(features) == 1
    _assert_point_feature(
        features[0],
        [
            "district_name", "province", "latitude", "longitude", "elevation_m",
            "river_distance_km", "slope_deg", "population_density_per_km2",
            "vulnerability_index",
        ],
    )
    props = features[0]["properties"]
    assert props["district_name"] == "Dadu"
    assert props["vulnerability_index"] == 0.8


def test_boundaries_graceful_when_table_missing(client, db):
    """404 with a clear message when district_boundaries is not migrated yet;
    a valid FeatureCollection once it exists."""
    user = make_user(db, role="public")
    headers = auth_headers(client, user)
    table_exists = "district_boundaries" in inspect(engine).get_table_names()

    res = client.get("/api/v1/gis/boundaries", headers=headers)
    if table_exists:
        assert res.status_code == 200
        _assert_feature_collection(res.json())
    else:
        assert res.status_code == 404
        assert "not loaded" in res.json()["detail"]
