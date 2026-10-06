#!/usr/bin/env python3
"""CSV/GeoJSON dataset importer CLI.

Usage:
    python scripts/import_csv.py --type flood_events --file data/events.csv
    python scripts/import_csv.py --type weather --file data/weather.csv --dry-run
    python scripts/import_csv.py --type geographic --file data/districts.csv
    python scripts/import_csv.py --type boundaries --file data/boundaries.geojson

Exit code is 1 when any row fails validation or the import errors.
"""

import argparse
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.services.importers import IMPORTERS, get_importer  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a dataset CSV/GeoJSON file into the flood-risk database."
    )
    parser.add_argument(
        "--type",
        dest="dataset",
        required=True,
        choices=sorted(IMPORTERS),
        help="Dataset to import.",
    )
    parser.add_argument("--file", required=True, help="Path to the input file.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and parse everything, then roll back without saving.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows per insert batch (default: 500).",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="Database URL (default: DATABASE_URL from backend/.env).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.database_url:
        print("error: DATABASE_URL is not set (backend/.env or --database-url)",
              file=sys.stderr)
        return 2

    importer_cls = get_importer(args.dataset)
    report = importer_cls().run(
        Session(create_engine(args.database_url)),
        args.file,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )

    print(f"Dataset : {report.dataset} (dry_run={report.dry_run})")
    print(f"File    : {args.file}")
    print(f"Rows    : total={report.total_rows} imported={report.imported} "
          f"duplicates_skipped={report.skipped_duplicates} "
          f"errors={len(report.errors)}")
    if report.errors:
        print("Errors  :")
        for entry in report.errors[:25]:
            print(f"  row {entry['row']}: {entry['message']}")
        if len(report.errors) > 25:
            print(f"  ... and {len(report.errors) - 25} more")
    return 1 if report.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
