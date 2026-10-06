"""Push notification delivery (Phase 6 early warning).

Uses Firebase Cloud Messaging via the firebase-admin SDK when a
service-account JSON is configured (FCM_SERVICE_ACCOUNT_PATH). When it is
not — the normal state for development and research deployments — the
service runs in degraded mode: notifications are logged instead of sent,
and every call reports ``delivered=False, mode="degraded"`` so callers can
tell the difference.

Production setup is documented in docs/early-warning-system.md.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import DeviceToken

logger = logging.getLogger("flood-risk-dss.notify")

_fcm_app = None
_fcm_error: str | None = None


def _init_fcm():
    """Initialise firebase-admin lazily; return (ok, reason)."""
    global _fcm_app, _fcm_error
    if _fcm_app is not None:
        return True, None
    if _fcm_error is not None:
        return False, _fcm_error
    path = settings.fcm_service_account_path
    if not path or not Path(path).is_file():
        _fcm_error = "no FCM service account configured (degraded mode)"
        return False, _fcm_error
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(path)
        _fcm_app = firebase_admin.initialize_app(cred)
        return True, None
    except Exception as exc:  # missing lib, bad JSON, network — all degrade
        _fcm_error = f"FCM init failed: {exc}"
        logger.warning(_fcm_error)
        return False, _fcm_error


def fcm_status() -> dict:
    ok, reason = _init_fcm()
    return {"mode": "fcm" if ok else "degraded", "detail": reason}


def _send_multicast(tokens: list[str], title: str, body: str, data: dict) -> dict:
    ok, reason = _init_fcm()
    if not ok:
        logger.warning(
            "[degraded notify] title=%r body=%r tokens=%d (%s)",
            title, body, len(tokens), reason,
        )
        return {"delivered": False, "mode": "degraded", "tokens": len(tokens), "detail": reason}
    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in data.items()},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        logger.info("FCM multicast: %d/%d delivered", response.success_count, len(tokens))
        return {
            "delivered": True,
            "mode": "fcm",
            "tokens": len(tokens),
            "success": response.success_count,
            "failure": response.failure_count,
        }
    except Exception as exc:
        logger.error("FCM send failed: %s", exc)
        return {"delivered": False, "mode": "fcm", "tokens": len(tokens), "detail": str(exc)}


def notify_district_users(
    db: Session,
    district_name: str,
    title: str,
    message: str,
    data: dict | None = None,
    platforms: list[str] | None = None,
) -> dict:
    """Notify all registered devices. (District targeting is a documented
    future step — see docs/early-warning-system.md; currently all tokens are
    notified because device locations are not stored.)"""
    query = db.query(DeviceToken)
    if platforms:
        query = query.filter(DeviceToken.platform.in_(platforms))
    tokens = [t.fcm_token for t in query.all()]
    if not tokens:
        logger.info("notify: no device tokens registered; alert logged only")
        return {"delivered": False, "mode": "none", "tokens": 0, "detail": "no tokens"}
    return _send_multicast(tokens, title, message, data or {})


def alert_notify_callback(db: Session):
    """Build the notify callback injected into the alert engine cycle."""

    def _notify(payload: dict) -> None:
        result = notify_district_users(
            db,
            payload["district_name"],
            payload["title"],
            payload["message"],
            data={
                "district": payload["district_name"],
                "level": payload["level"],
                "severity": payload["severity"],
                "probability": payload.get("probability"),
            },
        )
        logger.info("notify result for %s: %s", payload["district_name"], result.get("mode"))

    return _notify
