"""District-boundary GeoJSON importer.

Expected input: a GeoJSON FeatureCollection (or single Feature) where each
feature has:
  properties: { district_name*, province, source }
  geometry:   Polygon or MultiPolygon (WGS 84 coordinates)

Geometries are validated with shapely; invalid geometries are repaired with
make_valid when possible and rejected otherwise. Polygons are promoted to
MultiPolygon. Natural key: geographic_id (one boundary per district).
"""

from typing import Any

from geoalchemy2 import WKTElement
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid
from sqlalchemy.orm import Session

from app.models import DistrictBoundary
from app.services.importers.base import (
    DistrictResolver,
    GeoJSONImporter,
    RowValidationError,
    clean_str,
)


class BoundaryImporter(GeoJSONImporter):
    dataset_name = "boundaries"

    def prepare(self, session: Session) -> None:
        self.resolver = DistrictResolver(session)

    def _validate_geometry(self, geometry: dict | None, line_no: int) -> BaseGeometry:
        if not geometry:
            raise RowValidationError(f"row {line_no}: feature has no geometry")
        try:
            geom = shape(geometry)
        except Exception as exc:
            raise RowValidationError(
                f"row {line_no}: could not parse geometry: {exc}")
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            raise RowValidationError(
                f"row {line_no}: geometry must be Polygon or MultiPolygon "
                f"(got {geom.geom_type})")
        if geom.is_empty:
            raise RowValidationError(f"row {line_no}: geometry is empty")
        if not geom.is_valid:
            geom = make_valid(geom)
            if not geom.is_valid or geom.is_empty:
                raise RowValidationError(
                    f"row {line_no}: geometry is invalid and could not be repaired")
        # Promote Polygon to MultiPolygon for schema consistency.
        if geom.geom_type == "Polygon":
            from shapely.geometry import MultiPolygon
            geom = MultiPolygon([geom])
        return geom

    def parse_row(self, raw: dict[str, Any], line_no: int) -> dict[str, Any]:
        geographic_id = self.resolver.resolve(
            clean_str(raw.get("district_name"), "district_name",
                      required=True, line_no=line_no),
            clean_str(raw.get("province")),
            line_no=line_no,
        )
        geom = self._validate_geometry(raw.get("_geometry"), line_no)
        return {
            "geographic_id": geographic_id,
            "geom": WKTElement(geom.wkt, srid=4326),
            "source": clean_str(raw.get("source")),
        }

    def natural_key(self, values: dict[str, Any]) -> tuple:
        return (values["geographic_id"],)

    def exists(self, session: Session, values: dict[str, Any]) -> bool:
        query = session.query(DistrictBoundary.id).filter(
            DistrictBoundary.geographic_id == values["geographic_id"])
        return session.query(query.exists()).scalar()

    def make_object(self, values: dict[str, Any]) -> DistrictBoundary:
        return DistrictBoundary(**values)
