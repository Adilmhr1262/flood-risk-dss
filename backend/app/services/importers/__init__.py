"""Dataset importer registry."""

from app.services.importers.base import BaseImporter
from app.services.importers.boundaries import BoundaryImporter
from app.services.importers.flood_events import FloodEventImporter
from app.services.importers.geographic import GeographicImporter
from app.services.importers.weather import WeatherImporter

IMPORTERS: dict[str, type[BaseImporter]] = {
    "flood_events": FloodEventImporter,
    "weather": WeatherImporter,
    "geographic": GeographicImporter,
    "boundaries": BoundaryImporter,
}


def get_importer(dataset: str) -> type[BaseImporter] | None:
    """Return the importer class for a dataset name, or None if unknown."""
    return IMPORTERS.get(dataset)


__all__ = [
    "IMPORTERS",
    "BaseImporter",
    "BoundaryImporter",
    "FloodEventImporter",
    "GeographicImporter",
    "WeatherImporter",
    "get_importer",
]
