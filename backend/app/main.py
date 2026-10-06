"""Application factory and ASGI entrypoint."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings
from app.middleware import RateLimitMiddleware

logger = logging.getLogger("flood-risk-dss")


def configure_logging() -> None:
    """Timestamped application logging to stdout and optionally a file."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if settings.log_file:
        handlers.append(logging.FileHandler(settings.log_file))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=handlers,
        force=True,
    )


def _cors_options() -> dict:
    """Production-safe CORS: explicit origins with credentials, or open
    wildcard without credentials when CORS_ORIGINS=* (development)."""
    raw = (settings.cors_origins or "*").strip()
    if raw == "*":
        return {
            "allow_origins": ["*"],
            "allow_credentials": False,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type"],
    }


def _check_production_secrets() -> None:
    """Refuse to boot a production instance with placeholder secrets."""
    if settings.app_env != "production":
        return
    problems = []
    if settings.secret_key == "change-me-to-a-long-random-secret":
        problems.append("SECRET_KEY is still the placeholder value")
    if settings.cors_origins.strip() == "*":
        problems.append("CORS_ORIGINS=* is not allowed in production")
    if problems:
        raise RuntimeError(
            "Production safety checks failed: " + "; ".join(problems)
        )


def _run_scheduled_cycle() -> None:
    """One automated early-warning cycle (runs in a scheduler thread).

    Weather update -> prediction engine -> risk calculation -> alert decision.
    Every step is exception-safe so a bad cycle never kills the scheduler.
    """
    from app.db.session import SessionLocal
    from app.services import alert_engine, notifications, weather_ingestion

    db = SessionLocal()
    try:
        try:
            ingestion = weather_ingestion.ingest_all(
                db, forecast_days=settings.ew_forecast_days
            )
            logger.info("scheduled weather ingestion: %d new rows", ingestion["inserted"])
        except Exception as exc:
            logger.error("scheduled weather ingestion failed: %s", exc)
        try:
            summary = alert_engine.run_early_warning_cycle(
                db,
                model_name=settings.ew_default_model,
                cooldown_hours=settings.ew_alert_cooldown_hours,
                notify=notifications.alert_notify_callback(db),
            )
            logger.info(
                "scheduled early-warning cycle: %d districts, %d alerts",
                summary["districts_evaluated"],
                summary["alerts_issued"],
            )
        except Exception as exc:
            logger.error("scheduled early-warning cycle failed: %s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Flood Risk DSS backend started (env=%s)", settings.app_env)
    scheduler = None
    if settings.ew_scheduler_enabled:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            _run_scheduled_cycle,
            "interval",
            minutes=settings.ew_cycle_minutes,
            id="early_warning_cycle",
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info(
            "early-warning scheduler enabled: every %d min (model=%s, cooldown=%dh)",
            settings.ew_cycle_minutes,
            settings.ew_default_model,
            settings.ew_alert_cooldown_hours,
        )
    else:
        logger.info("early-warning scheduler disabled (EW_SCHEDULER_ENABLED=false)")
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("early-warning scheduler stopped")


def create_app() -> FastAPI:
    configure_logging()
    _check_production_secrets()

    app = FastAPI(
        title="Flood Risk Prediction and Early Warning Decision Support System",
        version="1.0.0",
        description=(
            "Data-driven flood risk prediction and early warning decision support "
            "for disaster management authorities, NGOs, and the public."
        ),
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.app_env != "production" else None,
    )

    app.add_middleware(CORSMiddleware, **_cors_options())
    app.add_middleware(RateLimitMiddleware)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        """Liveness probe: process is up. (Readiness details: /api/v1/status.)"""
        return {"status": "ok", "env": settings.app_env, "model_version": settings.model_version}

    @app.get("/api/v1/status")
    def service_status():
        """Readiness probe for monitoring: database, model registry, scheduler."""
        from sqlalchemy import text

        from app.db.session import SessionLocal

        db_ok = False
        db_error: str | None = None
        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                db_ok = True
            finally:
                db.close()
        except Exception as exc:  # noqa: BLE001 - surfaced in the status payload
            db_error = f"{type(exc).__name__}"
        try:
            from app.services.prediction_service import PredictionService

            models = PredictionService().available_models()
            model_info = {
                "name": settings.ew_default_model,
                "loaded": settings.ew_default_model in models,
                "available": sorted(models.keys()),
            }
        except Exception:  # noqa: BLE001 - degraded status is still informative
            model_info = {"name": settings.ew_default_model, "loaded": False, "available": []}
        overall = "ok" if db_ok else "degraded"
        return {
            "status": overall,
            "env": settings.app_env,
            "database": {"ok": db_ok, "error": db_error},
            "model": model_info,
            "scheduler": {
                "enabled": settings.ew_scheduler_enabled,
                "cycle_minutes": settings.ew_cycle_minutes,
            },
        }

    @app.get("/api/v1/early-warning/status")
    def early_warning_status():
        """Scheduler configuration and FCM mode (no secrets exposed)."""
        from app.services import notifications

        return {
            "scheduler_enabled": settings.ew_scheduler_enabled,
            "cycle_minutes": settings.ew_cycle_minutes,
            "alert_cooldown_hours": settings.ew_alert_cooldown_hours,
            "default_model": settings.ew_default_model,
            "notifications": notifications.fcm_status(),
        }

    return app


app = create_app()
