#!/usr/bin/env python3
"""Weather ingestion CLI (Phase 6 early warning).

Usage:
    python scripts/ingest_weather.py                      # all districts, once
    python scripts/ingest_weather.py --districts Dadu,Larkana
    python scripts/ingest_weather.py --forecast-days 3
    python scripts/ingest_weather.py --loop 4 --interval 1800   # 4 cycles, 30 min apart
"""

import argparse
import json
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.weather_ingestion import ingest_all  # noqa: E402


def run_once(districts: list[str] | None, forecast_days: int) -> dict:
    engine = create_engine(settings.database_url)
    with Session(engine) as db:
        return ingest_all(db, forecast_days=forecast_days, district_names=districts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Open-Meteo weather into weather_observations")
    parser.add_argument("--districts", default=None, help="Comma-separated district names (default: all)")
    parser.add_argument("--forecast-days", type=int, default=2)
    parser.add_argument("--loop", type=int, default=1, help="Number of ingestion cycles")
    parser.add_argument("--interval", type=int, default=1800, help="Seconds between cycles")
    args = parser.parse_args()

    districts = [d.strip() for d in args.districts.split(",")] if args.districts else None
    for cycle in range(args.loop):
        summary = run_once(districts, args.forecast_days)
        print(json.dumps({k: v for k, v in summary.items() if k != "per_district"}, indent=2))
        if cycle < args.loop - 1:
            time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
