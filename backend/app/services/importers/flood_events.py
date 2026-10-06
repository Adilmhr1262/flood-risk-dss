"""Historical flood-event CSV importer.

Expected columns (header row required):
  district_name*, province, event_date* (YYYY-MM-DD), rainfall_mm,
  temperature_c, humidity_pct, severity* (1-5), flood_status (true/false),
  damage_description, affected_population, source

Natural key: (geographic_id, event_date, source).
"""

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FloodEvent
from app.services.importers.base import (
    CSVImporter,
    DistrictResolver,
    clean_str,
    parse_bool,
    parse_date,
    parse_float,
    parse_int,
)


class FloodEventImporter(CSVImporter):
    dataset_name = "flood_events"
    required_columns = ("district_name", "event_date", "severity")

    def prepare(self, session: Session) -> None:
        self.resolver = DistrictResolver(session)

    def parse_row(self, raw: dict[str, Any], line_no: int) -> dict[str, Any]:
        geographic_id = self.resolver.resolve(
            clean_str(raw.get("district_name"), "district_name",
                      required=True, line_no=line_no),
            clean_str(raw.get("province")),
            line_no=line_no,
        )
        event_date: date = parse_date(
            raw.get("event_date"), "event_date", required=True, line_no=line_no)
        severity: int = parse_int(
            raw.get("severity"), "severity", required=True,
            min_value=1, max_value=5, line_no=line_no)
        return {
            "geographic_id": geographic_id,
            "event_date": event_date,
            "rainfall_mm": parse_float(raw.get("rainfall_mm"), "rainfall_mm",
                                       min_value=0, line_no=line_no),
            "temperature_c": parse_float(raw.get("temperature_c"), "temperature_c",
                                         min_value=-20, max_value=60, line_no=line_no),
            "humidity_pct": parse_float(raw.get("humidity_pct"), "humidity_pct",
                                        min_value=0, max_value=100, line_no=line_no),
            "severity": severity,
            "flood_status": parse_bool(raw.get("flood_status"), "flood_status",
                                       default=True, line_no=line_no),
            "damage_description": clean_str(raw.get("damage_description")),
            "affected_population": parse_int(raw.get("affected_population"),
                                             "affected_population",
                                             min_value=0, line_no=line_no),
            "source": clean_str(raw.get("source")),
        }

    def natural_key(self, values: dict[str, Any]) -> tuple:
        return (values["geographic_id"], values["event_date"],
                (values["source"] or "").lower())

    def exists(self, session: Session, values: dict[str, Any]) -> bool:
        query = session.query(FloodEvent.id).filter(
            FloodEvent.geographic_id == values["geographic_id"],
            FloodEvent.event_date == values["event_date"],
        )
        if values["source"]:
            query = query.filter(
                func.lower(FloodEvent.source) == values["source"].lower())
        else:
            query = query.filter(
                (FloodEvent.source.is_(None)) | (FloodEvent.source == ""))
        return session.query(query.exists()).scalar()

    def make_object(self, values: dict[str, Any]) -> FloodEvent:
        return FloodEvent(**values)
