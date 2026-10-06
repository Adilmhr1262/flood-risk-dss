"""Weather-observation CSV importer.

Expected columns (header row required):
  district_name*, province, observed_at* (ISO datetime, e.g.
  2022-08-15T06:00:00+00:00), rainfall_mm, temperature_c, humidity_pct,
  source

Natural key: (geographic_id, observed_at, source) — matches the UNIQUE
constraint on weather_observations.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import WeatherObservation
from app.services.importers.base import (
    CSVImporter,
    DistrictResolver,
    clean_str,
    parse_datetime,
    parse_float,
)


class WeatherImporter(CSVImporter):
    dataset_name = "weather"
    required_columns = ("district_name", "observed_at")

    def prepare(self, session: Session) -> None:
        self.resolver = DistrictResolver(session)

    def parse_row(self, raw: dict[str, Any], line_no: int) -> dict[str, Any]:
        geographic_id = self.resolver.resolve(
            clean_str(raw.get("district_name"), "district_name",
                      required=True, line_no=line_no),
            clean_str(raw.get("province")),
            line_no=line_no,
        )
        observed_at: datetime = parse_datetime(
            raw.get("observed_at"), "observed_at", required=True, line_no=line_no)
        return {
            "geographic_id": geographic_id,
            "observed_at": observed_at,
            "rainfall_mm": parse_float(raw.get("rainfall_mm"), "rainfall_mm",
                                       min_value=0, line_no=line_no),
            "temperature_c": parse_float(raw.get("temperature_c"), "temperature_c",
                                         min_value=-20, max_value=60, line_no=line_no),
            "humidity_pct": parse_float(raw.get("humidity_pct"), "humidity_pct",
                                        min_value=0, max_value=100, line_no=line_no),
            "source": clean_str(raw.get("source")) or "unknown",
        }

    def natural_key(self, values: dict[str, Any]) -> tuple:
        return (values["geographic_id"], values["observed_at"],
                values["source"].lower())

    def exists(self, session: Session, values: dict[str, Any]) -> bool:
        query = session.query(WeatherObservation.id).filter(
            WeatherObservation.geographic_id == values["geographic_id"],
            WeatherObservation.observed_at == values["observed_at"],
            WeatherObservation.source == values["source"],
        )
        return session.query(query.exists()).scalar()

    def make_object(self, values: dict[str, Any]) -> WeatherObservation:
        return WeatherObservation(**values)
