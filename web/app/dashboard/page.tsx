"use client";

import { useState } from "react";
import { BellRing, MapPinned, BarChart3, ShieldCheck } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { StatCard } from "@/components/StatCard";
import { AlertCard } from "@/components/AlertCard";
import { EmptyState } from "@/components/EmptyState";
import { MapComponent } from "@/components/MapComponent";
import { SituationHeader, type SituationHeaderData } from "@/components/SituationHeader";
import {
  EmergencyModeView,
  EmergencyModeToggle,
} from "@/components/EmergencyModeView";
import { RainfallChart } from "@/components/charts/RainfallChart";
import { FloodFrequencyChart } from "@/components/charts/FloodFrequencyChart";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApi } from "@/lib/api/hooks";
import { dashboardApi, alertsApi } from "@/lib/api/endpoints";
import { publicApi } from "@/lib/api/public";

const safetyTips = [
  {
    title: "Before the monsoon",
    items: [
      "Know your district's risk level on the map above and the nearest shelter.",
      "Keep drinking water, dry food, medicines, and documents in a waterproof bag.",
      "Save Rescue 1122 and your district PDMA helpline in your phone.",
    ],
  },
  {
    title: "During flooding",
    items: [
      "Move to higher ground immediately when a warning is issued — do not wait.",
      "Never walk or drive through flowing water; 15 cm can knock you down.",
      "Turn off electricity and gas if water enters your home.",
    ],
  },
  {
    title: "After the water recedes",
    items: [
      "Do not drink tap water until authorities declare it safe; boil if unsure.",
      "Check buildings for structural damage before re-entering.",
      "Report blocked roads and damaged infrastructure through the volunteer portal.",
    ],
  },
];

export default function PublicDashboardPage() {
  const summary = useApi(() => dashboardApi.summary());
  const alerts = useApi(() => alertsApi.list(1, 10, true));
  const situation = useApi(() => publicApi.situation());
  const [emergencyMode, setEmergencyMode] = useState(false);

  const headerData: SituationHeaderData | null = situation.data
    ? {
        activeAlerts: situation.data.active_alerts.length,
        emergencyAlerts: situation.data.active_alerts.filter(
          (a) => a.severity === "emergency",
        ).length,
        highRiskDistricts: situation.data.high_risk_districts.length,
        highRiskNames: situation.data.high_risk_districts.map(
          (d) => d.district_name,
        ),
        generatedAt: situation.data.generated_at,
      }
    : null;

  const riskAccent =
    summary.data?.current_risk_status === "HIGH"
      ? "red"
      : summary.data?.current_risk_status === "MEDIUM"
        ? "orange"
        : "emerald";

  return (
    <DashboardShell
      title="Public Dashboard"
      subtitle="Live flood risk overview for Sindh, Pakistan"
      actions={
        <EmergencyModeToggle
          active={emergencyMode}
          onToggle={() => setEmergencyMode((v) => !v)}
        />
      }
    >
      {emergencyMode ? (
        <EmergencyModeView
          situation={situation.data}
          alerts={alerts.data?.items ?? []}
          onExit={() => setEmergencyMode(false)}
        />
      ) : (
        <>
          {/* Live flood situation header */}
          <SituationHeader
            data={headerData}
            loading={situation.loading}
            alertsHref="/dashboard#alerts"
            mapHref="/map"
          />

          {/* Interactive action cards */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Active Flood Alerts"
              value={summary.data?.active_alerts ?? "—"}
              hint="alerts currently in force — click to open alert centre"
              icon={BellRing}
              accent="red"
              loading={summary.loading}
              href="/dashboard#alerts"
            />
            <StatCard
              label="High Risk Areas"
              value={summary.data?.high_risk_areas ?? "—"}
              hint="districts at HIGH risk — click to open risk map"
              icon={MapPinned}
              accent="orange"
              loading={summary.loading}
              href="/map"
            />
            <StatCard
              label="Historical Events"
              value={summary.data?.total_historical_events ?? "—"}
              hint="recorded flood events — click to open flood timeline"
              icon={BarChart3}
              accent="navy"
              loading={summary.loading}
              href="/map?layer=history"
            />
            <StatCard
              label="Current Risk Status"
              value={summary.data?.current_risk_status ?? "—"}
              hint="worst active level"
              icon={ShieldCheck}
              accent={riskAccent as "red" | "orange" | "emerald"}
              loading={summary.loading}
            />
          </div>
      {summary.error && (
        <p className="mt-3 text-sm text-red-600">
          Live overview unavailable: {summary.error}
        </p>
      )}

      {/* Risk map */}
      <section id="risk-map" className="mt-8 scroll-mt-28">
        <h2 className="mb-3 text-lg font-semibold text-navy-950">
          District Risk Map
        </h2>
        <MapComponent className="h-[480px]" />
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-red-600" /> High risk
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-amber-500" /> Medium risk
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-emerald-500" /> Low risk
          </span>
        </div>
      </section>

      {/* Charts */}
      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <RainfallChart />
        <FloodFrequencyChart />
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <RiskDistributionChart />
        <Card>
          <CardHeader>
            <CardTitle className="text-base">About these figures</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-slate-600">
            <p>
              Charts are computed live from the platform&apos;s research
              dataset: 180 district-year records covering 12 districts from
              2010 to 2024, with flood events verified against NDMA, PDMA, and
              relief-agency sources. Risk levels combine machine-learning
              flood probability with district vulnerability indicators.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      <section id="alerts" className="mt-8 scroll-mt-28">
        <h2 className="mb-3 text-lg font-semibold text-navy-950">
          Active Alerts
        </h2>
        {alerts.loading && (
          <div className="space-y-3">
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </div>
        )}
        {alerts.error && (
          <p className="text-sm text-red-600">
            Alerts unavailable: {alerts.error}
          </p>
        )}
        {alerts.data && alerts.data.items.length === 0 && (
          <EmptyState
            title="No active alerts"
            description="There are no flood alerts in force right now. The early-warning watch runs continuously through the monsoon season."
            actionLabel="Refresh"
            onAction={alerts.refetch}
          />
        )}
        {alerts.data && alerts.data.items.length > 0 && (
          <div className="space-y-3">
            {alerts.data.items.map((a) => (
              <AlertCard key={a.id} alert={a} />
            ))}
          </div>
        )}
      </section>

      {/* Safety guidance */}
      <section id="safety" className="mt-8 scroll-mt-28">
        <h2 className="mb-3 text-lg font-semibold text-navy-950">
          Safety Guidance
        </h2>
        <div className="grid gap-5 md:grid-cols-3">
          {safetyTips.map((t) => (
            <Card key={t.title}>
              <CardHeader>
                <CardTitle className="text-base">{t.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm leading-relaxed text-slate-600">
                  {t.items.map((i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                      {i}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
        </>
      )}
    </DashboardShell>
  );
}
