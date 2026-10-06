"""Application configuration via environment variables.

Field names match backend/.env (case-insensitive):
DATABASE_URL, TEST_DATABASE_URL, SECRET_KEY, JWT_ALGORITHM,
ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, CORS_ORIGINS, APP_ENV.
Phase 6 early-warning settings: EW_SCHEDULER_ENABLED, EW_CYCLE_MINUTES,
EW_ALERT_COOLDOWN_HOURS, EW_DEFAULT_MODEL, EW_FORECAST_DAYS.
Phase W4 production hardening: RATE_LIMIT_PER_MINUTE,
RATE_LIMIT_AUTH_PER_MINUTE, LOG_FILE.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg2://flood_user:changeme@localhost:5432/flood_dss"
    test_database_url: str = "postgresql+psycopg2://flood_user:changeme@localhost:5432/flood_dss_test"
    secret_key: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    cors_origins: str = "*"
    model_version: str = "v1.0.0-rule-based"

    # Production hardening (Phase W4).
    # Rate limits: requests per minute per client IP (sliding window).
    rate_limit_per_minute: int = 120
    rate_limit_auth_per_minute: int = 20
    # Optional path for the application log file (in addition to stdout).
    log_file: str | None = None

    # Phase 6 — automated early warning cycle.
    ew_scheduler_enabled: bool = False
    ew_cycle_minutes: int = 30
    ew_alert_cooldown_hours: int = 6
    ew_default_model: str = "mlp-v1"
    ew_forecast_days: int = 2
    # Path to a Firebase service-account JSON for FCM push. When unset or
    # missing, notifications run in degraded (log-only) mode.
    fcm_service_account_path: str | None = None


settings = Settings()
