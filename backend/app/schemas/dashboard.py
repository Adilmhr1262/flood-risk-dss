"""Dashboard aggregate schemas."""

from pydantic import BaseModel


class SummaryCards(BaseModel):
    active_alerts: int
    high_risk_areas: int
    total_historical_events: int
    current_risk_status: str  # worst active level: LOW / MEDIUM / HIGH


class TrendPoint(BaseModel):
    period: str  # e.g. "2026-09" or "2024"
    rainfall_mm: float


class FrequencyPoint(BaseModel):
    period: str
    events: int


class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int
