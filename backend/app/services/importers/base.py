"""Data import framework: validation, duplicate detection, batching, reports.

Each dataset gets an importer subclass that declares:
  - required_columns: CSV headers that must be present
  - parse_row(): validate + normalize one raw row into ORM-ready values
  - natural_key(): tuple identifying a row for duplicate detection
  - exists(): database duplicate check on the natural key
  - make_object(): build the ORM object from parsed values

Imports run in batches; a failed batch is rolled back and its rows are
reported as errors while the rest of the file continues. dry_run mode
parses and validates everything but rolls back instead of committing.
"""

from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import GeographicData


class RowValidationError(ValueError):
    """A single input row failed validation."""


class HeaderError(ValueError):
    """The file header is missing required columns."""


@dataclass
class ImportReport:
    """Result of one import run."""

    dataset: str
    total_rows: int = 0
    imported: int = 0
    skipped_duplicates: int = 0
    errors: list[dict] = field(default_factory=list)
    dry_run: bool = False

    def add_error(self, row: int | str, message: str) -> None:
        self.errors.append({"row": row, "message": str(message)})

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "total_rows": self.total_rows,
            "imported": self.imported,
            "skipped_duplicates": self.skipped_duplicates,
            "error_count": len(self.errors),
            "errors": self.errors,
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# Parsing / validation helpers
# ---------------------------------------------------------------------------

def clean_str(value: Any, field_name: str = "", *, required: bool = False,
              line_no: int = 0) -> str | None:
    text = "" if value is None else str(value).strip()
    if not text:
        if required:
            raise RowValidationError(f"row {line_no}: '{field_name}' is required")
        return None
    return text


def parse_float(value: Any, field_name: str, *, required: bool = False,
                min_value: float | None = None, max_value: float | None = None,
                line_no: int = 0) -> float | None:
    text = clean_str(value, field_name, required=required, line_no=line_no)
    if text is None:
        return None
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        raise RowValidationError(f"row {line_no}: '{field_name}' is not a number (got '{text}')")
    if min_value is not None and number < min_value:
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be >= {min_value} (got {number})")
    if max_value is not None and number > max_value:
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be <= {max_value} (got {number})")
    return number


def parse_int(value: Any, field_name: str, *, required: bool = False,
              min_value: int | None = None, max_value: int | None = None,
              line_no: int = 0) -> int | None:
    number = parse_float(value, field_name, required=required, line_no=line_no)
    if number is None:
        return None
    if not number.is_integer():
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be an integer (got '{value}')")
    ivalue = int(number)
    if min_value is not None and ivalue < min_value:
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be >= {min_value} (got {ivalue})")
    if max_value is not None and ivalue > max_value:
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be <= {max_value} (got {ivalue})")
    return ivalue


def parse_date(value: Any, field_name: str, *, required: bool = False,
               line_no: int = 0) -> date | None:
    text = clean_str(value, field_name, required=required, line_no=line_no)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be YYYY-MM-DD (got '{text}')")


def parse_datetime(value: Any, field_name: str, *, required: bool = False,
                   line_no: int = 0) -> datetime | None:
    text = clean_str(value, field_name, required=required, line_no=line_no)
    if text is None:
        return None
    candidate = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        raise RowValidationError(
            f"row {line_no}: '{field_name}' must be ISO datetime (got '{text}')")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


TRUE_VALUES = {"true", "1", "yes", "y", "t"}
FALSE_VALUES = {"false", "0", "no", "n", "f"}


def parse_bool(value: Any, field_name: str, *, default: bool = True,
               line_no: int = 0) -> bool:
    text = clean_str(value, field_name, line_no=line_no)
    if text is None:
        return default
    lowered = text.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise RowValidationError(
        f"row {line_no}: '{field_name}' must be true/false (got '{text}')")


# ---------------------------------------------------------------------------
# District resolution
# ---------------------------------------------------------------------------

class DistrictResolver:
    """Resolves (district_name[, province]) to a geographic_data id."""

    def __init__(self, session: Session) -> None:
        self._by_both: dict[tuple[str, str], UUID] = {}
        self._by_district: dict[str, list[UUID]] = {}
        for row in session.query(
            GeographicData.id, GeographicData.district_name, GeographicData.province
        ).all():
            gid, district, province = row
            self._by_both[(district.strip().lower(), province.strip().lower())] = gid
            self._by_district.setdefault(district.strip().lower(), []).append(gid)

    def resolve(self, district_name: str | None, province: str | None = None,
                line_no: int = 0) -> UUID:
        if not district_name:
            raise RowValidationError(f"row {line_no}: 'district_name' is required")
        district = district_name.strip().lower()
        if province:
            key = (district, province.strip().lower())
            gid = self._by_both.get(key)
            if gid is None:
                raise RowValidationError(
                    f"row {line_no}: unknown district '{district_name}' "
                    f"in province '{province}'")
            return gid
        matches = self._by_district.get(district, [])
        if not matches:
            raise RowValidationError(
                f"row {line_no}: unknown district '{district_name}'")
        if len(matches) > 1:
            raise RowValidationError(
                f"row {line_no}: district '{district_name}' is ambiguous "
                f"({len(matches)} matches); specify province")
        return matches[0]


# ---------------------------------------------------------------------------
# Importer base classes
# ---------------------------------------------------------------------------

class BaseImporter(ABC):
    """Template for dataset importers."""

    dataset_name: str = "base"

    # -- hooks ------------------------------------------------------------
    def prepare(self, session: Session) -> None:
        """Preload lookups (e.g. district maps) before reading rows."""

    @abstractmethod
    def read_records(self, path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
        """Yield (line_no, raw_record) pairs from the input file."""

    @abstractmethod
    def parse_row(self, raw: dict[str, Any], line_no: int) -> dict[str, Any]:
        """Validate + normalize one raw record into ORM-ready values."""

    @abstractmethod
    def natural_key(self, values: dict[str, Any]) -> tuple:
        """Tuple identifying a record for duplicate detection."""

    @abstractmethod
    def exists(self, session: Session, values: dict[str, Any]) -> bool:
        """True when the natural key is already in the database."""

    @abstractmethod
    def make_object(self, values: dict[str, Any]) -> Any:
        """Build the ORM object from parsed values."""

    # -- driver -----------------------------------------------------------
    def run(self, session: Session, path: str | Path, *, dry_run: bool = False,
            batch_size: int = 500) -> ImportReport:
        report = ImportReport(dataset=self.dataset_name, dry_run=dry_run)
        path = Path(path)
        if not path.is_file():
            report.add_error("-", f"file not found: {path}")
            return report

        self.prepare(session)
        try:
            records = list(self.read_records(path))
        except HeaderError as exc:
            report.add_error("-", str(exc))
            return report
        except (OSError, json.JSONDecodeError, csv.Error) as exc:
            report.add_error("-", f"could not read file: {exc}")
            return report

        seen: set[tuple] = set()
        buffer: list[tuple[int, tuple, Any]] = []  # (line_no, key, orm_obj)

        def flush() -> None:
            if not buffer:
                return
            # SAVEPOINT per batch: a failed batch rolls back only its own
            # rows, leaving previously flushed batches intact.
            savepoint = session.begin_nested()
            try:
                session.add_all(obj for _, _, obj in buffer)
                session.flush()
                report.imported += len(buffer)
            except Exception as exc:  # noqa: BLE001 - report, then continue
                savepoint.rollback()
                for key in [key for _, key, _ in buffer]:
                    seen.discard(key)
                for line_no, _, _ in buffer:
                    report.add_error(line_no, f"batch insert failed: {exc}")
            buffer.clear()

        for line_no, raw in records:
            report.total_rows += 1
            try:
                values = self.parse_row(raw, line_no)
            except RowValidationError as exc:
                report.add_error(line_no, str(exc))
                continue
            key = self.natural_key(values)
            try:
                duplicate = key in seen or self.exists(session, values)
            except Exception as exc:  # noqa: BLE001 - report, then continue
                report.add_error(line_no, f"duplicate check failed: {exc}")
                continue
            if duplicate:
                report.skipped_duplicates += 1
                continue
            seen.add(key)
            try:
                buffer.append((line_no, key, self.make_object(values)))
            except Exception as exc:  # noqa: BLE001 - report, then continue
                seen.discard(key)
                report.add_error(line_no, f"could not build record: {exc}")
            if len(buffer) >= batch_size:
                flush()

        flush()

        if dry_run:
            session.rollback()
        else:
            try:
                session.commit()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                report.add_error("-", f"commit failed: {exc}")
        return report


class CSVImporter(BaseImporter):
    """Importer for CSV files with a header row."""

    required_columns: tuple[str, ...] = ()

    def _validate_header(self, fieldnames: list[str] | None, path: Path) -> None:
        if not fieldnames:
            raise HeaderError(f"{path.name}: file has no header row")
        normalized = {name.strip().lower() for name in fieldnames if name}
        missing = [col for col in self.required_columns if col.lower() not in normalized]
        if missing:
            raise HeaderError(
                f"{path.name}: missing required column(s): {', '.join(missing)}")

    def read_records(self, path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            self._validate_header(reader.fieldnames, path)
            for row in reader:
                # Skip fully-blank lines.
                if not any((value or "").strip() for value in row.values()):
                    continue
                normalized = {
                    (key.strip().lower() if key else ""): value
                    for key, value in row.items()
                }
                yield reader.line_num, normalized


class GeoJSONImporter(BaseImporter):
    """Importer for GeoJSON FeatureCollections (one record per feature)."""

    def read_records(self, path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and data.get("type") == "Feature":
            features = [data]
        elif isinstance(data, dict) and data.get("type") == "FeatureCollection":
            features = data.get("features", [])
        else:
            raise HeaderError(
                f"{path.name}: expected a GeoJSON Feature or FeatureCollection")
        for index, feature in enumerate(features, start=1):
            props = feature.get("properties") or {}
            record = {str(k).strip().lower(): v for k, v in props.items()}
            record["_geometry"] = feature.get("geometry")
            yield index, record
