"""Schema exports."""

from app.schemas.alert import AlertCreate, AlertOut
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.boundary import DistrictBoundaryOut
from app.schemas.citizen_report import (
    CitizenReportCreate,
    CitizenReportOut,
    CitizenReportVerify,
    DeviceTokenCreate,
    DeviceTokenOut,
)
from app.schemas.command_center import (
    IncidentCreate,
    IncidentNoteCreate,
    IncidentNoteOut,
    IncidentOut,
    IncidentStats,
    IncidentStatusUpdate,
    ResponseTeamCreate,
    ResponseTeamOut,
    ResponseTeamUpdate,
    ShelterResourceOut,
    ShelterUpdate,
    WeatherLatestOut,
)
from app.schemas.common import PaginatedResponse, Pagination
from app.schemas.dashboard import FrequencyPoint, RiskDistribution, SummaryCards, TrendPoint
from app.schemas.decision_support import (
    InfrastructureOut,
    ResourceAllocationCreate,
    ResourceAllocationOut,
    VulnerabilityIndicatorOut,
)
from app.schemas.emergency_contact import EmergencyContactOut
from app.schemas.geographic import GeographicOut
from app.schemas.gis import GeoJSONFeature, GeoJSONFeatureCollection
from app.schemas.risk import PredictionOut, RiskAssessmentInput, RiskAssessmentOutput
from app.schemas.shelter import ShelterOut
from app.schemas.user import UserOut, UserUpdate
from app.schemas.weather import WeatherObservationOut

__all__ = [
    "AlertCreate",
    "AlertOut",
    "CitizenReportCreate",
    "CitizenReportOut",
    "CitizenReportVerify",
    "DeviceTokenCreate",
    "DeviceTokenOut",
    "DistrictBoundaryOut",
    "LoginRequest",
    "RefreshRequest",
    "RegisterRequest",
    "ResourceAllocationCreate",
    "ResourceAllocationOut",
    "TokenResponse",
    "PaginatedResponse",
    "Pagination",
    "EmergencyContactOut",
    "FrequencyPoint",
    "GeographicOut",
    "IncidentCreate",
    "IncidentNoteCreate",
    "IncidentNoteOut",
    "IncidentOut",
    "IncidentStats",
    "IncidentStatusUpdate",
    "InfrastructureOut",
    "ResponseTeamCreate",
    "ResponseTeamOut",
    "ResponseTeamUpdate",
    "RiskDistribution",
    "ShelterOut",
    "ShelterResourceOut",
    "ShelterUpdate",
    "SummaryCards",
    "TrendPoint",
    "WeatherLatestOut",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "PredictionOut",
    "RiskAssessmentInput",
    "RiskAssessmentOutput",
    "UserOut",
    "UserUpdate",
    "VulnerabilityIndicatorOut",
    "WeatherObservationOut",
]
