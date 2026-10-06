"""Tests for the dataset import system.

Database-backed tests run against TEST_DATABASE_URL (the empty
flood_risk_dss_test database with migrations applied). Tables touched by the
importers are truncated before each test for isolation.
"""

import csv
import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip("TEST_DATABASE_URL is not set", allow_module_level=True)

import app.models  # noqa: E402,F401 - register all models on Base.metadata
from app.db.base import Base  # noqa: E402
from app.models import DistrictBoundary, FloodEvent, GeographicData, WeatherObservation  # noqa: E402
from app.services.importers import get_importer  # noqa: E402
from app.services.importers.base import (  # noqa: E402
    HeaderError,
    RowValidationError,
    parse_bool,
    parse_date,
    parse_datetime,
    parse_float,
    parse_int,
)

pytestmark = pytest.mark.db

TRUNCATE_SQL = text(
    "TRUNCATE geographic_data, flood_events, weather_observations, "
    "district_boundaries RESTART IDENTITY CASCADE"
)


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(eng, checkfirst=True)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    with engine.begin() as conn:
        conn.execute(TRUNCATE_SQL)
    session = Session(engine)
    yield session
    session.close()


def write_csv(path: Path, header: list[str], rows: list[list]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def seed_district(db: Session, name: str = "Dadu", province: str = "Sindh") -> None:
    importer = get_importer("geographic")()
    report = importer.run(db, BACKEND_DIR.parent / "datasets" / "templates" / "geographic.csv")
    assert not report.has_errors, report.errors
    assert db.query(GeographicData).count() == 2


# ---------------------------------------------------------------------------
# flood_events
# ---------------------------------------------------------------------------

EVENT_HEADER = ["district_name", "province", "event_date", "rainfall_mm",
                "temperature_c", "humidity_pct", "severity", "flood_status",
                "damage_description", "affected_population", "source"]


def test_flood_event_validation_errors(db, tmp_path):
    seed_district(db)
    path = write_csv(tmp_path / "bad.csv", EVENT_HEADER, [
        ["Dadu", "Sindh", "2022-08-15", "180", "34", "82", "9", "true", "", "", "NDMA"],  # severity 9
        ["Dadu", "Sindh", "not-a-date", "180", "34", "82", "4", "true", "", "", "NDMA"],  # bad date
        ["UnknownDistrict", "Sindh", "2022-08-15", "180", "34", "82", "4", "true", "", "", "NDMA"],  # unknown
    ])
    report = get_importer("flood_events")().run(db, path)
    assert report.total_rows == 3
    assert report.imported == 0
    assert len(report.errors) == 3
    assert db.query(FloodEvent).count() == 0


def test_flood_event_duplicate_detection(db, tmp_path):
    seed_district(db)
    path = write_csv(tmp_path / "events.csv", EVENT_HEADER, [
        ["Dadu", "Sindh", "2022-08-15", "180.5", "34.0", "82.0", "5", "true", "breaches", "125000", "NDMA report"],
        ["Larkana", "Sindh", "2022-08-20", "165.0", "33.5", "85.0", "4", "true", "", "98000", "PDMA Sindh"],
        # in-file duplicate of row 1 (same natural key)
        ["Dadu", "Sindh", "2022-08-15", "180.5", "34.0", "82.0", "5", "true", "breaches", "125000", "NDMA report"],
    ])
    importer = get_importer("flood_events")()
    first = importer.run(db, path)
    assert first.imported == 2, first.to_dict()
    assert first.skipped_duplicates == 1
    assert not first.has_errors

    second = importer.run(db, path)
    assert second.imported == 0
    assert second.skipped_duplicates == 3
    assert db.query(FloodEvent).count() == 2


def test_flood_event_missing_header(db, tmp_path):
    path = write_csv(tmp_path / "noheader.csv", ["district_name", "foo"], [["Dadu", "x"]])
    report = get_importer("flood_events")().run(db, path)
    assert report.total_rows == 0
    assert report.has_errors
    assert "event_date" in report.errors[0]["message"]


# ---------------------------------------------------------------------------
# geographic + dry-run
# ---------------------------------------------------------------------------

def test_geographic_dry_run_persists_nothing(db):
    importer = get_importer("geographic")()
    path = BACKEND_DIR.parent / "datasets" / "templates" / "geographic.csv"
    report = importer.run(db, path, dry_run=True)
    assert report.dry_run is True
    assert report.imported == 2
    assert not report.has_errors
    assert db.query(GeographicData).count() == 0


def test_geographic_duplicate_detection(db):
    importer = get_importer("geographic")()
    path = BACKEND_DIR.parent / "datasets" / "templates" / "geographic.csv"
    first = importer.run(db, path)
    assert first.imported == 2
    second = importer.run(db, path)
    assert second.imported == 0
    assert second.skipped_duplicates == 2


# ---------------------------------------------------------------------------
# weather
# ---------------------------------------------------------------------------

def test_weather_import_and_duplicates(db):
    seed_district(db)
    importer = get_importer("weather")()
    path = BACKEND_DIR.parent / "datasets" / "templates" / "weather.csv"
    first = importer.run(db, path)
    assert first.imported == 2, first.to_dict()
    second = importer.run(db, path)
    assert second.imported == 0
    assert second.skipped_duplicates == 2
    assert db.query(WeatherObservation).count() == 2


def test_weather_validation_errors(db, tmp_path):
    seed_district(db)
    path = write_csv(tmp_path / "weather.csv",
                     ["district_name", "province", "observed_at", "rainfall_mm",
                      "temperature_c", "humidity_pct", "source"],
                     [["Dadu", "Sindh", "2022-08-15T06:00:00+00:00", "-5", "34", "88", "PMD"]])
    report = get_importer("weather")().run(db, path)
    assert report.imported == 0
    assert len(report.errors) == 1
    assert "rainfall_mm" in report.errors[0]["message"]


# ---------------------------------------------------------------------------
# boundaries (GeoJSON)
# ---------------------------------------------------------------------------

def _geojson(path: Path, features: list[dict]) -> Path:
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


def _feature(district: str, geometry: dict, province: str = "Sindh") -> dict:
    return {
        "type": "Feature",
        "properties": {"district_name": district, "province": province,
                       "source": "test"},
        "geometry": geometry,
    }


SQUARE = {"type": "Polygon",
          "coordinates": [[[67.5, 26.5], [68.0, 26.5], [68.0, 27.0],
                            [67.5, 27.0], [67.5, 26.5]]]}


def test_boundary_geojson_import(db, tmp_path):
    seed_district(db)
    path = _geojson(tmp_path / "bounds.geojson", [
        _feature("Dadu", SQUARE),
        _feature("Larkana", SQUARE),
        _feature("Dadu", SQUARE),  # duplicate of feature 1
        _feature("Dadu", {"type": "Point", "coordinates": [67.7, 26.7]}),  # bad type
        _feature("NoSuchDistrict", SQUARE),  # unknown district
    ])
    report = get_importer("boundaries")().run(db, path)
    assert report.total_rows == 5, report.to_dict()
    assert report.imported == 2, report.to_dict()
    assert report.skipped_duplicates == 1
    assert len(report.errors) == 2
    assert db.query(DistrictBoundary).count() == 2
    # Geometry stored as MultiPolygon.
    geom_type = db.execute(
        text("SELECT GeometryType(geom) FROM district_boundaries LIMIT 1")
    ).scalar()
    assert geom_type == "MULTIPOLYGON"


def test_boundary_template_imports_cleanly(db):
    seed_district(db)
    path = BACKEND_DIR.parent / "datasets" / "templates" / "boundaries.geojson"
    report = get_importer("boundaries")().run(db, path)
    assert report.imported == 2, report.to_dict()
    assert not report.has_errors


# ---------------------------------------------------------------------------
# parse helpers (no database needed)
# ---------------------------------------------------------------------------

def test_parse_helpers():
    assert parse_float("12.5", "f", line_no=1) == 12.5
    assert parse_float("", "f", line_no=1) is None
    with pytest.raises(RowValidationError):
        parse_float("abc", "f", line_no=3)
    with pytest.raises(RowValidationError):
        parse_float("-1", "f", min_value=0, line_no=3)

    assert parse_int("5", "f", line_no=1) == 5
    with pytest.raises(RowValidationError):
        parse_int("5.5", "f", line_no=1)

    assert parse_date("2022-08-15", "f", line_no=1).isoformat() == "2022-08-15"
    with pytest.raises(RowValidationError):
        parse_date("15/08/2022", "f", line_no=1)

    assert parse_datetime("2022-08-15T06:00:00+00:00", "f", line_no=1).tzinfo is not None
    with pytest.raises(RowValidationError):
        parse_datetime("yesterday", "f", line_no=1)

    assert parse_bool("yes", "f", line_no=1) is True
    assert parse_bool("0", "f", line_no=1) is False
    assert parse_bool("", "f", line_no=1) is True
    with pytest.raises(RowValidationError):
        parse_bool("maybe", "f", line_no=1)
