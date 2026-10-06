"""v1 API router aggregator."""

from fastapi import APIRouter

from app.api.v1 import admin, alerts, auth, dashboard, decision_support, gis, incidents, mobile, public, reports, resources, risk, users, weather

api_router = APIRouter()

api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(decision_support.router, prefix="/decision-support", tags=["decision-support"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(gis.router, prefix="/gis", tags=["gis"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(mobile.router, prefix="/mobile", tags=["mobile"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
