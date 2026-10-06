"""Geographic-data CSV importer.

Expected columns (header row required):
  district_name*, province*, latitude* (-90..90), longitude* (-180..180),
  elevation_m (>=0), river_distance_km (>=0), slope_deg (0-90),
  population_density_per_km2 (>=0), vulnerability_index (0-1)

The PostGIS point geometry is built from latitude/longitude. Natural key:
(district_name, province) — existing districts are skipped as duplicates.
"""

from typing import Any

from geoalchemy2 import WKTElement
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import GeographicData
from app.services.importers.base import (
    CSVImporter,
    clean_str,
    parse_float,
)


class GeographicImporter(CSVImporter):
    dataset_name = "geographic"
    required_columns = ("district_name", "province", "latitude", "longitude")

    def parse_row(self, raw: dict[str, Any], line_no: int) -> dict[str, Any]:
        district_name = clean_str(raw.get("district_name"), "district_name",
                                  required=True, line_no=line_no)
        province = clean_str(raw.get("province"), "province",
                             required=True, line_no=line_no)
        latitude = parse_float(raw.get("latitude"), "latitude", required=True,
                               min_value=-90, max_value=90, line_no=line_no)
        longitude = parse_float(raw.get("longitude"), "longitude", required=True,
                                min_value=-180, max_value=180, line_no=line_no)
        return {
            "district_name": district_name,
            "province": province,
            "latitude": latitude,
            "longitude": longitude,
            "geom": WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            "elevation_m": parse_float(raw.get("elevation_m"), "elevation_m",
                                       min_value=0, line_no=line_no),
            "river_distance_km": parse_float(raw.get("river_distance_km"),
                                             "river_distance_km",
                                             min_value=0, line_no=line_no),
            "slope_deg": parse_float(raw.get("slope_deg"), "slope_deg",
                                     min_value=0, max_value=90, line_no=line_no),
            "population_density_per_km2": parse_float(
                raw.get("population_density_per_km2"), "population_density_per_km2",
                min_value=0, line_no=line_no),
            "vulnerability_index": parse_float(raw.get("vulnerability_index"),
                                               "vulnerability_index",
                                               min_value=0, max_value=1,
                                               line_no=line_no),
        }

    def natural_key(self, values: dict[str, Any]) -> tuple:
        return (values["district_name"].lower(), values["province"].lower())

    def exists(self, session: Session, values: dict[str, Any]) -> bool:
        query = session.query(GeographicData.id).filter(
            func.lower(GeographicData.district_name) == values["district_name"].lower(),
            func.lower(GeographicData.province) == values["province"].lower(),
        )
        return session.query(query.exists()).scalar()

    def make_object(self, values: dict[str, Any]) -> GeographicData:
        return GeographicData(**values)
