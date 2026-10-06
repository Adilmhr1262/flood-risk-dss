"""Risk assessment input/output schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RiskAssessmentInput(BaseModel):
    district_name: str = Field(min_length=2, max_length=150)
    rainfall_mm: float = Field(ge=0, le=2000)
    temperature_c: float = Field(ge=-30, le=60)
    humidity_pct: float = Field(ge=0, le=100)
    elevation_m: float = Field(ge=-500, le=9000)
    river_distance_km: float = Field(ge=0, le=1000)
    slope_deg: float = Field(ge=0, le=90)
    population_density: float = Field(ge=0, le=100000)
    prev_flood_events: int = Field(ge=0, le=100)
    last_severity: int = Field(ge=0, le=5, description="Severity of most recent flood: 0=None, 1=Minor, 2=Moderate, 3=Severe, 4=Very severe, 5=Catastrophic (matches flood_events.severity)")
    vulnerability_index: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Provisional district vulnerability composite (0-1, see "
        "data/processed/DATA_CARD.md). Optional: when omitted, the Phase 3 "
        "models fall back to the training median.",
    )


class FeatureContribution(BaseModel):
    """One row of the contribution-based explanation for a prediction."""

    feature: str
    contribution: float  # normalised to sum to 1 over the top features
    value: float  # the (preprocessed, engineered) feature value that was scored


class RiskAssessmentOutput(BaseModel):
    district_name: str
    probability: float  # 0-1, percentage shown as probability * 100
    risk_level: str  # LOW / MEDIUM / HIGH
    main_factors: list[str]
    recommendations: list[str]
    model_version: str
    prediction_id: UUID | None = None
    model_requested: str | None = None
    note: str | None = None  # set when falling back to the rule-based engine
    feature_contributions: list[FeatureContribution] = []  # top contributing features (ML models only)


class PredictionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    geographic_id: UUID
    probability: float
    risk_level: str
    main_factors: list[str] = []
    recommendations: list[str] = []
    model_version: str
    predicted_at: datetime
