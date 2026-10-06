"""Automated alert decision engine (Phase 6 early warning).

Alert rule table:
    LOW    -> no alert
    MEDIUM -> advisory notification  (alerts.severity = 'watch')
    HIGH   -> emergency warning      (alerts.severity = 'emergency')

Deduplication / escalation:
    - A district does not get a second alert at the same level within
      EW_ALERT_COOLDOWN_HOURS (default 6h).
    - Escalation (MEDIUM -> HIGH) always issues immediately, even inside the
      cooldown window, and deactivates the superseded advisory.

The engine is driven by run_early_warning_cycle(), which the APScheduler job
and the manual CLI both call. Notifications are delivered through an injected
notify callback so the engine stays testable without Firebase.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models import Alert, FloodEvent, GeographicData, WeatherObservation
from app.schemas.risk import RiskAssessmentInput
from app.services.prediction_service import PredictionService
from app.services.risk_engine import risk_level

logger = logging.getLogger("flood-risk-dss.alerts")

# risk level -> alerts.severity value (None = no alert issued)
LEVEL_TO_SEVERITY = {
    "LOW": None,
    "MEDIUM": "watch",
    "HIGH": "emergency",
}

LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

ALERT_TITLES = {
    "MEDIUM": "Flood advisory",
    "HIGH": "FLOOD EMERGENCY WARNING",
}


def _district_weather_features(db: Session, district: GeographicData, hours: int = 24) -> dict:
    """Aggregate recent + forecast weather into prediction inputs.

    rainfall_mm uses the maximum forecast precipitation over the next 24h —
    early warning must react to what is coming, not only what has fallen.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=6)
    horizon = datetime.now(timezone.utc) + timedelta(hours=hours)
    rows = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.geographic_id == district.id,
            WeatherObservation.observed_at >= since,
            WeatherObservation.observed_at <= horizon,
            WeatherObservation.source == "open-meteo",
        )
        .all()
    )
    rainfall = max((r.rainfall_mm or 0.0) for r in rows) if rows else 0.0
    temps = [r.temperature_c for r in rows if r.temperature_c is not None]
    hums = [r.humidity_pct for r in rows if r.humidity_pct is not None]
    return {
        "rainfall_mm": round(rainfall, 1),
        "temperature_c": round(sum(temps) / len(temps), 1) if temps else 30.0,
        "humidity_pct": round(sum(hums) / len(hums), 1) if hums else 70.0,
        "n_observations": len(rows),
    }


def _district_history(db: Session, district: GeographicData) -> dict:
    count = (
        db.query(func.count(FloodEvent.id))
        .filter(FloodEvent.geographic_id == district.id)
        .scalar()
        or 0
    )
    last_sev = (
        db.query(func.max(FloodEvent.severity))
        .filter(FloodEvent.geographic_id == district.id)
        .scalar()
        or 0
    )
    return {"prev_flood_events": int(count), "last_severity": int(last_sev)}


def _recent_alert(db: Session, geographic_id, cooldown_hours: int) -> Alert | None:
    """Most recent active alert for the district inside the cooldown window."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
    return (
        db.query(Alert)
        .filter(
            Alert.geographic_id == geographic_id,
            Alert.is_active.is_(True),
            Alert.issued_at >= cutoff,
        )
        .order_by(desc(Alert.issued_at))
        .first()
    )


def decide(district_name: str, assessment: dict) -> dict | None:
    """Apply the alert rule table to one assessment.

    Returns an alert payload dict, or None when the level is LOW.
    """
    level = assessment["risk_level"]
    severity = LEVEL_TO_SEVERITY.get(level)
    if severity is None:
        return None
    factors = assessment.get("main_factors") or []
    return {
        "title": f"{ALERT_TITLES[level]}: {district_name}",
        "message": (
            f"{district_name} risk is {level} "
            f"(probability {assessment['probability']:.0%}). "
            f"Key factors: {', '.join(factors[:4]) or 'under review'}. "
            f"Recommended: {'; '.join((assessment.get('recommendations') or [])[:2])}."
        ),
        "severity": severity,
        "level": level,
    }


def issue_alert(
    db: Session,
    district: GeographicData,
    decision: dict,
    assessment: dict,
    notify: Callable[[dict], None] | None = None,
) -> Alert:
    """Persist an alert and fan out notifications."""
    alert = Alert(
        geographic_id=district.id,
        title=decision["title"],
        message=decision["message"],
        severity=decision["severity"],
        model_version=assessment.get("model_version"),
        probability=assessment.get("probability"),
        factors=list(assessment.get("main_factors") or []),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.warning("ALERT issued: %s [%s]", alert.title, alert.severity)
    if notify is not None:
        try:
            notify(
                {
                    "district_name": district.district_name,
                    "level": decision["level"],
                    "severity": decision["severity"],
                    "title": decision["title"],
                    "message": decision["message"],
                    "probability": assessment.get("probability"),
                }
            )
        except Exception as exc:  # notifications must never break the cycle
            logger.error("notification fan-out failed: %s", exc)
    return alert


def evaluate_district(
    db: Session,
    district: GeographicData,
    service: PredictionService,
    model_name: str,
    cooldown_hours: int,
    notify: Callable[[dict], None] | None = None,
) -> dict:
    """Run one district through weather -> prediction -> alert decision."""
    weather = _district_weather_features(db, district)
    history = _district_history(db, district)
    inputs = RiskAssessmentInput(
        district_name=district.district_name,
        rainfall_mm=weather["rainfall_mm"],
        temperature_c=weather["temperature_c"],
        humidity_pct=weather["humidity_pct"],
        elevation_m=district.elevation_m or 0.0,
        river_distance_km=district.river_distance_km or 0.0,
        slope_deg=district.slope_deg or 0.0,
        population_density=district.population_density_per_km2 or 0.0,
        prev_flood_events=history["prev_flood_events"],
        last_severity=history["last_severity"],
        vulnerability_index=district.vulnerability_index,
    )
    assessment = service.assess(district.district_name, inputs, model_name=model_name)
    # Provenance: record the registry model name that was requested, not the
    # engine's internal version string.
    assessment["model_version"] = model_name
    decision = decide(district.district_name, assessment)
    outcome = {
        "district": district.district_name,
        "risk_level": assessment["risk_level"],
        "probability": assessment["probability"],
        "model_version": assessment.get("model_version"),
        "alert_issued": False,
    }
    if decision is None:
        return outcome

    recent = _recent_alert(db, district.id, cooldown_hours)
    if recent is not None:
        recent_level = "HIGH" if recent.severity == "emergency" else "MEDIUM"
        if LEVEL_RANK[decision["level"]] <= LEVEL_RANK[recent_level]:
            outcome["skipped"] = f"cooldown: {recent_level} alert already active"
            return outcome
        # Escalation: retire the superseded advisory before issuing.
        recent.is_active = False
        db.commit()
        outcome["escalated_from"] = recent_level

    alert = issue_alert(db, district, decision, assessment, notify=notify)
    outcome["alert_issued"] = True
    outcome["alert_id"] = str(alert.id)
    outcome["severity"] = alert.severity
    return outcome


def run_early_warning_cycle(
    db: Session,
    model_name: str = "rule-based-v1",
    cooldown_hours: int = 6,
    district_names: list[str] | None = None,
    notify: Callable[[dict], None] | None = None,
) -> dict:
    """Full cycle: weather -> prediction -> alert decision -> notify.

    Returns a per-district outcome summary. Safe to call from the scheduler,
    a CLI, or tests (pass a fake notify in tests).
    """
    query = db.query(GeographicData).order_by(GeographicData.district_name)
    if district_names:
        lowered = [n.strip().lower() for n in district_names]
        query = query.filter(func.lower(GeographicData.district_name).in_(lowered))
    districts = query.all()

    service = PredictionService(db=db)
    outcomes: list[dict] = []
    for district in districts:
        try:
            outcomes.append(
                evaluate_district(db, district, service, model_name, cooldown_hours, notify)
            )
        except Exception as exc:
            logger.error("cycle failed for %s: %s", district.district_name, exc)
            outcomes.append({"district": district.district_name, "error": str(exc)})

    issued = sum(1 for o in outcomes if o.get("alert_issued"))
    summary = {
        "districts_evaluated": len(outcomes),
        "alerts_issued": issued,
        "model": model_name,
        "outcomes": outcomes,
    }
    logger.info(
        "early warning cycle complete: %d districts, %d alerts", len(outcomes), issued
    )
    return summary
