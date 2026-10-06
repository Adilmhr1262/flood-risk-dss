"""Automated weather ingestion (Phase 6 early warning).

Pulls current + hourly forecast weather from the Open-Meteo forecast API
(free, no key required) for every district centroid in `geographic_data`
and stores rows in `weather_observations` with source='open-meteo'.

The natural-key UNIQUE constraint on (geographic_id, observed_at, source)
makes repeated runs duplicate-safe: re-ingesting the same hour is a no-op.

Stored per district per run:
  - one "current conditions" row (observed_at = fetch time, hourly values
    interpolated by Open-Meteo to the current hour), and
  - hourly forecast rows for the next ``forecast_days`` days, so the alert
    engine can score near-term risk from forecast rainfall.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import GeographicData, WeatherObservation

logger = logging.getLogger("flood-risk-dss.weather")

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
SOURCE = "open-meteo"
REQUEST_TIMEOUT_S = 30
POLITENESS_SLEEP_S = 1.0  # be polite to the free API between districts


def _fetch_district(lat: float, lon: float, forecast_days: int) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    with httpx.Client(timeout=REQUEST_TIMEOUT_S) as client:
        resp = client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        return resp.json()


def _bulk_upsert(db: Session, rows: list[dict]) -> int:
    """Insert-or-ignore a batch of observation dicts. Returns rows inserted."""
    if not rows:
        return 0
    stmt = pg_insert(WeatherObservation).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["geographic_id", "observed_at", "source"]
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0


def ingest_district(
    db: Session,
    district_id: UUID,
    lat: float,
    lon: float,
    forecast_days: int = 2,
) -> dict:
    """Fetch and store weather for one district. Returns counts."""
    payload = _fetch_district(lat, lon, forecast_days)
    now = datetime.now(timezone.utc)
    rows: list[dict] = []

    current = payload.get("current") or {}
    if current.get("time"):
        rows.append(
            {
                "geographic_id": district_id,
                "observed_at": datetime.fromisoformat(current["time"]),
                "rainfall_mm": current.get("precipitation"),
                "temperature_c": current.get("temperature_2m"),
                "humidity_pct": current.get("relative_humidity_2m"),
                "source": SOURCE,
            }
        )

    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    hums = hourly.get("relative_humidity_2m") or []
    precs = hourly.get("precipitation") or []
    for i, t in enumerate(times):
        rows.append(
            {
                "geographic_id": district_id,
                "observed_at": datetime.fromisoformat(t),
                "rainfall_mm": precs[i] if i < len(precs) else None,
                "temperature_c": temps[i] if i < len(temps) else None,
                "humidity_pct": hums[i] if i < len(hums) else None,
                "source": SOURCE,
            }
        )

    inserted = _bulk_upsert(db, rows)
    logger.info(
        "ingested district_id=%s: %d rows (%d new)", district_id, len(rows), inserted
    )
    return {"district_id": str(district_id), "rows": len(rows), "inserted": inserted}


def ingest_all(
    db: Session,
    forecast_days: int = 2,
    district_names: list[str] | None = None,
) -> dict:
    """Ingest weather for all districts (or a named subset)."""
    query = db.query(GeographicData)
    if district_names:
        lowered = [n.strip().lower() for n in district_names]
        query = query.filter(func.lower(GeographicData.district_name).in_(lowered))
    districts = query.order_by(GeographicData.district_name).all()

    total_rows = 0
    total_inserted = 0
    per_district: list[dict] = []
    for i, d in enumerate(districts):
        try:
            result = ingest_district(db, d.id, d.latitude, d.longitude, forecast_days)
        except Exception as exc:  # one bad district must not stop the cycle
            logger.warning("ingest failed for %s: %s", d.district_name, exc)
            result = {"district_id": str(d.id), "rows": 0, "inserted": 0, "error": str(exc)}
        total_rows += result["rows"]
        total_inserted += result["inserted"]
        per_district.append({"district_name": d.district_name, **result})
        if i < len(districts) - 1:
            time.sleep(POLITENESS_SLEEP_S)

    summary = {
        "districts": len(districts),
        "rows": total_rows,
        "inserted": total_inserted,
        "source": SOURCE,
        "per_district": per_district,
    }
    logger.info("weather ingestion complete: %s", {k: v for k, v in summary.items() if k != "per_district"})
    return summary
