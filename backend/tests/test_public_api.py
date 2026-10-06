"""Public (unauthenticated) API tests: the FloodSafe Pakistan website surface.

Every endpoint here must work WITHOUT an Authorization header.
"""

from .conftest import make_contact, make_district, make_event


def test_public_situation_no_auth(client, db):
    make_district(db, name="Dadu")
    res = client.get("/api/v1/public/situation")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "high_risk_districts" in body
    assert "active_alerts" in body
    assert "latest_predictions" in body
    assert "generated_at" in body
    # No role-restricted data leaks into the public payload.
    assert "allocations" not in body


def test_public_risk_check_no_auth(client, db):
    make_district(db, name="Dadu")
    res = client.get("/api/v1/public/risk-check", params={"district_name": "Dadu"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["district_name"] == "Dadu"
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(body["main_factors"], list) and body["main_factors"]
    assert isinstance(body["recommendations"], list) and body["recommendations"]
    assert "inputs_used" in body
    assert "checked_at" in body


def test_public_risk_check_unknown_district(client, db):
    res = client.get("/api/v1/public/risk-check", params={"district_name": "Nowhere"})
    assert res.status_code == 404


def test_public_risk_check_does_not_persist(client, db):
    """Anonymous checks must not pollute the predictions table."""
    from app.models import Prediction

    make_district(db, name="Dadu")
    before = db.query(Prediction).count()
    res = client.get("/api/v1/public/risk-check", params={"district_name": "Dadu"})
    assert res.status_code == 200
    assert db.query(Prediction).count() == before


def test_public_map_risk_zones_no_auth(client, db):
    make_district(db, name="Dadu")
    res = client.get("/api/v1/public/map/risk-zones")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) >= 1


def test_public_map_resources_no_auth(client, db):
    from geoalchemy2 import WKTElement

    from app.models import Infrastructure

    district = make_district(db, name="Dadu")
    db.add(
        Infrastructure(
            name="Dadu Rescue Centre",
            type="rescue_center",
            geographic_id=district.id,
            geom=WKTElement("POINT(67.79 26.74)", srid=4326),
            contact_phone="+92-300-0000000",
            is_sample_data=False,
        )
    )
    db.commit()
    res = client.get("/api/v1/public/map/resources", params={"type": "rescue_center"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) >= 1


def test_public_map_resources_shelter_uses_shelter_registry(client, db):
    """?type=shelter must serve the shelters table, not the infrastructure table."""
    from geoalchemy2 import WKTElement

    from app.models import Shelter

    district = make_district(db, name="Dadu")
    db.add(
        Shelter(
            name="Dadu Test Relief Camp",
            geographic_id=district.id,
            geom=WKTElement("POINT(67.79 26.74)", srid=4326),
            capacity=500,
            contact_phone="+92-300-1111111",
        )
    )
    db.commit()
    res = client.get("/api/v1/public/map/resources", params={"type": "shelter"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["type"] == "FeatureCollection"
    names = [f["properties"]["name"] for f in body["features"]]
    assert "Dadu Test Relief Camp" in names

    res = client.get(
        "/api/v1/public/map/resources",
        params={"type": "shelter", "district_name": "dadu"},
    )
    assert res.status_code == 200, res.text
    names = [f["properties"]["name"] for f in res.json()["features"]]
    assert "Dadu Test Relief Camp" in names

    res = client.get(
        "/api/v1/public/map/resources",
        params={"type": "shelter", "district_name": "nonexistent-district"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["features"] == []


def test_public_emergency_contacts_no_auth(client, db):
    make_contact(db)
    res = client.get("/api/v1/public/emergency-contacts")
    assert res.status_code == 200, res.text
    body = res.json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_public_districts_no_auth(client, db):
    make_district(db, name="Dadu")
    make_district(db, name="Larkana")
    res = client.get("/api/v1/public/districts")
    assert res.status_code == 200, res.text
    body = res.json()
    names = [d["district_name"] for d in body["districts"]]
    assert "Dadu" in names and "Larkana" in names
    assert body["count"] == len(names)


def test_public_historical_floods_no_auth(client, db):
    district = make_district(db, name="Dadu")
    make_event(db, district)
    res = client.get("/api/v1/public/historical-floods")
    assert res.status_code == 200, res.text
    assert res.json()["type"] == "FeatureCollection"
