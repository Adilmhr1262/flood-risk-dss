/**
 * TypeScript types mirroring the Flood Risk DSS FastAPI backend
 * (backend/app/schemas). Keep in sync with the backend Pydantic models.
 */

export type Role = "authority" | "ngo" | "public" | "volunteer";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: Role;
}

export interface UserOut {
  id: string;
  name: string;
  email: string;
  role: Role;
  location_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role?: Role;
  location_name?: string | null;
}

/* ---------- Dashboard ---------- */

export interface SummaryCards {
  active_alerts: number;
  high_risk_areas: number;
  total_historical_events: number;
  /** Worst active level: LOW / MEDIUM / HIGH */
  current_risk_status: string;
}

export interface TrendPoint {
  period: string;
  rainfall_mm: number;
}

export interface FrequencyPoint {
  period: string;
  events: number;
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
}

/* ---------- Risk ---------- */

export interface RiskPredictInput {
  district_name: string;
  rainfall_mm: number;
  temperature_c: number;
  humidity_pct: number;
  river_discharge?: number | null;
  soil_moisture?: number | null;
  elevation_m: number;
  population_density?: number | null;
  vulnerability_index?: number | null;
}

export interface FeatureContribution {
  feature: string;
  contribution: number;
}

export interface RiskAssessmentOutput {
  district_name: string;
  /** 0–1 */
  probability: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  main_factors: string[];
  recommendations: string[];
  model_version: string;
  prediction_id: string | null;
  model_requested: string | null;
  note: string | null;
  feature_contributions: FeatureContribution[];
}

/* ---------- Alerts ---------- */

export type AlertSeverity = "info" | "watch" | "warning" | "emergency";

export interface AlertOut {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  is_active: boolean;
  geographic_id: string;
  issued_at: string;
  expires_at: string | null;
  model_version: string | null;
  probability: number | null;
  factors: unknown[] | null;
}

export interface AlertCreate {
  district_name: string;
  title: string;
  message: string;
  severity?: AlertSeverity;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/* ---------- GIS ---------- */

export interface GeoJSONFeature {
  type: "Feature";
  geometry: {
    type: string;
    coordinates: unknown;
  };
  properties: Record<string, unknown>;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

export interface EmergencyContact {
  id: string;
  name: string;
  organization: string | null;
  phone: string;
  district_name?: string | null;
}

/* ---------- Decision support ---------- */

export interface TopFactor {
  feature: string;
  contribution: number | null;
}

export interface HighRiskDistrict {
  district_name: string;
  province: string;
  probability: number;
  risk_level: string;
  model_version: string;
  predicted_at: string | null;
  top_factors: TopFactor[];
  recommended_actions: string[];
}

export interface DecisionAlert {
  id: string;
  title: string;
  message: string;
  severity: string;
  district_name: string;
  issued_at: string | null;
}

export interface DecisionSupportSummary {
  high_risk_districts: HighRiskDistrict[];
  active_alerts: DecisionAlert[];
  latest_predictions: HighRiskDistrict[];
  resource_overview: Record<string, unknown>;
  vulnerability_hotspots: Array<{
    district_name: string;
    province: string;
    vulnerability_index: number;
    population_density: number | null;
    risk_level: string | null;
    priority: string;
  }>;
  allocations: Array<{
    id: string;
    district_name: string | null;
    resource_type: string;
    quantity: number | null;
    status: string;
  }>;
}

/* ---------- Citizen reports ---------- */

export type ReportCategory =
  | "flood_water"
  | "road_blockage"
  | "rescue_request"
  | "medical_emergency";

export interface CitizenReportCreate {
  district_name: string;
  category: ReportCategory;
  description: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface CitizenReportOut {
  id: string;
  district_name: string | null;
  category: string;
  description: string;
  severity?: number;
  status: "pending" | "verified" | "rejected" | "resolved";
  priority?: ReportPriority;
  created_at: string;
}

/* ---------- API errors ---------- */

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed (${status})`);
    this.status = status;
    this.detail = detail;
  }
}

/* ---------- Command center (Phase W3, authority only) ---------- */

export type IncidentStatus =
  | "detected"
  | "verified"
  | "response_started"
  | "resolved";

export interface IncidentNoteOut {
  id: string;
  author_id: string | null;
  note: string;
  created_at: string;
}

export interface IncidentOut {
  id: string;
  title: string;
  description: string | null;
  district_name: string | null;
  status: IncidentStatus;
  severity: number;
  source: "manual" | "alert" | "report";
  created_by: string | null;
  assigned_to: string | null;
  notes: IncidentNoteOut[];
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface IncidentCreate {
  title: string;
  description?: string | null;
  district_name?: string | null;
  severity?: number;
  source?: "manual" | "alert" | "report";
  source_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface IncidentStats {
  by_status: Record<string, number>;
  open_by_severity: Record<string, number>;
  avg_hours_to_resolve: number | null;
  resolved_last_7d: number;
}

export interface ShelterResource {
  id: string;
  name: string;
  district_name: string | null;
  capacity: number | null;
  current_occupancy: number;
  availability: number | null;
  occupancy_pct: number | null;
  status: "open" | "full" | "closed" | "maintenance";
  contact_phone: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface ResponseTeam {
  id: string;
  name: string;
  team_type: "rescue" | "medical" | "logistics" | "boat";
  district_name: string | null;
  members_count: number | null;
  status: "available" | "deployed" | "standby";
  contact_phone: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  updated_at: string;
}

export interface ResponseTeamCreate {
  name: string;
  team_type: "rescue" | "medical" | "logistics" | "boat";
  district_name?: string | null;
  members_count?: number | null;
  status?: "available" | "deployed" | "standby";
  contact_phone?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface InfrastructureResource {
  id: string;
  name: string;
  type: string;
  district_name: string | null;
  capacity: number | null;
  contact_phone: string | null;
  operational_status: string;
  is_sample_data: boolean;
  latitude: number | null;
  longitude: number | null;
}

export interface WeatherLatest {
  district_name: string;
  observed_at: string | null;
  rainfall_mm: number | null;
  temperature_c: number | null;
  humidity_pct: number | null;
  source: string | null;
}

export type ReportPriority = "low" | "medium" | "high" | "urgent";

export interface ReportVerify {
  status: "pending" | "verified" | "rejected" | "resolved";
  note?: string | null;
  priority?: ReportPriority | null;
}
