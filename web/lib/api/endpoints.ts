/**
 * Typed endpoint wrappers for the Flood Risk DSS FastAPI backend.
 * Every function maps 1:1 to a backend route — no invented endpoints.
 */
import { apiRequest } from "./client";
import type {
  AlertCreate,
  AlertOut,
  CitizenReportCreate,
  CitizenReportOut,
  DecisionSupportSummary,
  EmergencyContact,
  FrequencyPoint,
  GeoJSONFeatureCollection,
  IncidentCreate,
  IncidentNoteOut,
  IncidentOut,
  IncidentStats,
  IncidentStatus,
  InfrastructureResource,
  LoginRequest,
  PaginatedResponse,
  RegisterRequest,
  ReportVerify,
  ResponseTeam,
  ResponseTeamCreate,
  RiskAssessmentOutput,
  RiskDistribution,
  RiskPredictInput,
  ShelterResource,
  SummaryCards,
  TokenResponse,
  TrendPoint,
  UserOut,
  WeatherLatest,
} from "./types";

/* ---------- Auth ---------- */

export const authApi = {
  login: (payload: LoginRequest) =>
    apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: payload,
      auth: false,
    }),
  register: (payload: RegisterRequest) =>
    apiRequest<TokenResponse>("/auth/register", {
      method: "POST",
      body: payload,
      auth: false,
    }),
  me: () => apiRequest<UserOut>("/auth/me"),
  logout: () => apiRequest<void>("/auth/logout", { method: "POST" }),
};

/* ---------- Dashboard ---------- */

export const dashboardApi = {
  summary: () => apiRequest<SummaryCards>("/dashboard/summary"),
  rainfallTrends: () => apiRequest<TrendPoint[]>("/dashboard/rainfall-trends"),
  floodFrequency: () => apiRequest<FrequencyPoint[]>("/dashboard/flood-frequency"),
  riskDistribution: () => apiRequest<RiskDistribution>("/dashboard/risk-distribution"),
};

/* ---------- Risk ---------- */

export const riskApi = {
  predict: (input: RiskPredictInput, model?: string) =>
    apiRequest<RiskAssessmentOutput>("/risk/predict", {
      method: "POST",
      body: input,
      query: model ? { model } : undefined,
    }),
  modelInfo: () => apiRequest<Record<string, unknown>>("/risk/model-info"),
};

/* ---------- Alerts ---------- */

export const alertsApi = {
  list: (page = 1, pageSize = 20, activeOnly = true) =>
    apiRequest<PaginatedResponse<AlertOut>>("/alerts", {
      query: { page, page_size: pageSize, active_only: activeOnly },
    }),
  create: (payload: AlertCreate) =>
    apiRequest<AlertOut>("/alerts", { method: "POST", body: payload }),
  deactivate: (id: string) =>
    apiRequest<AlertOut>(`/alerts/${id}/deactivate`, { method: "PATCH" }),
};

/* ---------- GIS ---------- */

export const gisApi = {
  riskLayer: () => apiRequest<GeoJSONFeatureCollection>("/gis/risk-layer"),
  vulnerabilityMap: () =>
    apiRequest<GeoJSONFeatureCollection>("/gis/vulnerability-map"),
  shelters: () => apiRequest<GeoJSONFeatureCollection>("/gis/shelters"),
  emergencyContacts: () =>
    apiRequest<EmergencyContact[]>("/gis/emergency-contacts"),
  districts: () => apiRequest<GeoJSONFeatureCollection>("/gis/districts"),
  historicalFloods: () =>
    apiRequest<GeoJSONFeatureCollection>("/gis/historical-floods"),
};

/* ---------- Decision support (authority / NGO) ---------- */

export const decisionSupportApi = {
  summary: () => apiRequest<DecisionSupportSummary>("/decision-support/summary"),
  trends: () =>
    apiRequest<Record<string, unknown>>("/decision-support/trends"),
};

/* ---------- Citizen reporting (volunteer / public / NGO) ---------- */

export const reportsApi = {
  submit: (payload: CitizenReportCreate) =>
    apiRequest<CitizenReportOut>("/mobile/report-event", {
      method: "POST",
      body: payload,
    }),
  mine: () => apiRequest<CitizenReportOut[]>("/mobile/reports/mine"),
};

/* ---------- Command center: incidents (authority only) ---------- */

export const incidentsApi = {
  list: (params?: { status?: string; district_name?: string; severity?: number }) =>
    apiRequest<IncidentOut[]>("/incidents", {
      query: params as Record<string, string | number> | undefined,
    }),
  get: (id: string) => apiRequest<IncidentOut>(`/incidents/${id}`),
  create: (payload: IncidentCreate) =>
    apiRequest<IncidentOut>("/incidents", { method: "POST", body: payload }),
  updateStatus: (id: string, status: IncidentStatus, note?: string) =>
    apiRequest<IncidentOut>(`/incidents/${id}/status`, {
      method: "PATCH",
      body: { status, note },
    }),
  addNote: (id: string, note: string) =>
    apiRequest<IncidentNoteOut>(`/incidents/${id}/notes`, {
      method: "POST",
      body: { note },
    }),
  stats: () => apiRequest<IncidentStats>("/incidents/stats"),
  map: (activeOnly = true) =>
    apiRequest<GeoJSONFeatureCollection>("/incidents/map", {
      query: { active_only: activeOnly },
    }),
};

/* ---------- Command center: resources (authority only) ---------- */

export const resourcesApi = {
  shelters: () => apiRequest<ShelterResource[]>("/resources/shelters"),
  updateShelter: (id: string, payload: { current_occupancy?: number; status?: string }) =>
    apiRequest<ShelterResource>(`/resources/shelters/${id}`, {
      method: "PATCH",
      body: payload,
    }),
  teams: (status?: string) =>
    apiRequest<ResponseTeam[]>("/resources/teams", {
      query: status ? { status } : undefined,
    }),
  createTeam: (payload: ResponseTeamCreate) =>
    apiRequest<ResponseTeam>("/resources/teams", { method: "POST", body: payload }),
  updateTeam: (id: string, payload: Partial<ResponseTeamCreate> & { status?: string }) =>
    apiRequest<ResponseTeam>(`/resources/teams/${id}`, {
      method: "PATCH",
      body: payload,
    }),
  deleteTeam: (id: string) =>
    apiRequest<void>(`/resources/teams/${id}`, { method: "DELETE" }),
  infrastructure: (type?: string) =>
    apiRequest<InfrastructureResource[]>("/resources/infrastructure", {
      query: type ? { type } : undefined,
    }),
};

/* ---------- Command center: weather + report triage (authority only) ---------- */

export const weatherApi = {
  latest: () => apiRequest<WeatherLatest[]>("/weather/latest"),
};

export const adminApi = {
  reports: (params?: { status?: string; category?: string; district_name?: string }) =>
    apiRequest<CitizenReportOut[]>("/admin/reports", {
      query: params as Record<string, string> | undefined,
    }),
  verifyReport: (id: string, payload: ReportVerify) =>
    apiRequest<CitizenReportOut>(`/admin/reports/${id}/verify`, {
      method: "PATCH",
      body: payload,
    }),
  reportsMap: (status?: string) =>
    apiRequest<GeoJSONFeatureCollection>("/admin/reports/map", {
      query: status ? { status } : undefined,
    }),
};
