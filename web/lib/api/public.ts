"use client";

/**
 * Public (unauthenticated) API client for the FloodSafe Pakistan website.
 *
 * Wraps the backend /api/v1/public/* endpoints — the same public-safety
 * data the authenticated API serves, available without a login so ordinary
 * citizens can check flood risk and find help during an emergency.
 */

import { apiBase } from "./client";
import { ApiError } from "./types";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface SituationDistrict {
  district_name: string;
  province: string | null;
  probability: number;
  risk_level: RiskLevel;
  model_version: string | null;
  predicted_at: string | null;
  top_factors: { feature: string; contribution: number }[];
  recommended_actions: string[];
}

export interface SituationAlert {
  id: string;
  title: string;
  message: string;
  severity: string;
  district_name: string;
  issued_at: string | null;
}

export interface SituationResponse {
  high_risk_districts: SituationDistrict[];
  active_alerts: SituationAlert[];
  latest_predictions: {
    district_name: string;
    province: string | null;
    probability: number;
    risk_level: RiskLevel;
    model_version: string | null;
    predicted_at: string | null;
  }[];
  resource_overview: {
    shelters: { count: number; total_capacity: number };
    infrastructure_by_type: Record<string, number>;
  };
  vulnerability_hotspots: {
    district_name: string;
    province: string | null;
    vulnerability_index: number;
    population_density: number | null;
    risk_level: RiskLevel | null;
    priority: string;
  }[];
  generated_at: string;
}

export interface RiskCheckResponse {
  district_name: string;
  province: string | null;
  probability: number;
  risk_level: RiskLevel;
  model_version: string;
  main_factors: string[];
  recommendations: string[];
  feature_contributions: { feature: string; contribution: number }[];
  inputs_used: {
    rainfall_mm: number;
    temperature_c: number;
    humidity_pct: number;
    prev_flood_events: number;
    last_severity: number;
  };
  note: string | null;
  checked_at: string;
}

export interface PublicDistrict {
  district_name: string;
  province: string | null;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    geometry: { type: string; coordinates: number[] | number[][][] };
    properties: Record<string, unknown>;
  }[];
}

export interface EmergencyContact {
  id: string;
  organization: string;
  name: string | null;
  phone: string;
  district_name: string | null;
}

async function publicGet<T>(path: string, query?: Record<string, string>): Promise<T> {
  const url = new URL(apiBase() + path);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== "") url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new ApiError(res.status, detail || res.statusText);
  }
  return (await res.json()) as T;
}

export const publicApi = {
  situation: () => publicGet<SituationResponse>("/public/situation"),
  serviceStatus: () =>
    publicGet<{
      status: string;
      env: string;
      database: { ok: boolean; error: string | null };
      model: { name: string; loaded: boolean; available: string[] };
      scheduler: { enabled: boolean; cycle_minutes: number };
    }>("/status"),
  riskCheck: (districtName: string) =>
    publicGet<RiskCheckResponse>("/public/risk-check", { district_name: districtName }),
  districts: () => publicGet<{ districts: PublicDistrict[]; count: number }>("/public/districts"),
  riskZones: () => publicGet<GeoJSONFeatureCollection>("/public/map/risk-zones"),
  resources: (type?: string, districtName?: string) =>
    publicGet<GeoJSONFeatureCollection>("/public/map/resources", {
      type: type ?? "",
      district_name: districtName ?? "",
    }),
  emergencyContacts: (districtName?: string) =>
    publicGet<EmergencyContact[]>("/public/emergency-contacts", {
      district_name: districtName ?? "",
    }),
  historicalFloods: (districtName?: string) =>
    publicGet<GeoJSONFeatureCollection>("/public/historical-floods", {
      district_name: districtName ?? "",
    }),
};

export const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: "#16a34a",
  MEDIUM: "#f59e0b",
  HIGH: "#dc2626",
};

export const RESOURCE_COLORS: Record<string, string> = {
  shelter: "#2563eb",
  hospital: "#db2777",
  rescue_center: "#ea580c",
  emergency_facility: "#7c3aed",
};
