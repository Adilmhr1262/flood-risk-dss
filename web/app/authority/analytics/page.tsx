"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CommandNav } from "@/components/authority/CommandNav";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/api/hooks";
import { formatProbability } from "@/lib/format";
import { adminApi, alertsApi, decisionSupportApi, incidentsApi } from "@/lib/api/endpoints";

interface TrendsPayload {
  year_wise: Array<{
    district_name: string;
    yearly: Array<{ year: number; events: number; avg_severity: number | null }>;
    total_events: number;
    trend_2017_2024_vs_2010_2016: string;
  }>;
  seasonal_pattern: Array<{ month: number; events: number }>;
  note: string;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function SectionCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const trends = useApi(() => decisionSupportApi.trends() as unknown as Promise<TrendsPayload>);
  const summary = useApi(() => decisionSupportApi.summary());
  const alertHistory = useApi(() => alertsApi.list(1, 50, false));
  const incidentStats = useApi(() => incidentsApi.stats());
  const incidents = useApi(() => incidentsApi.list());
  const reports = useApi(() => adminApi.reports());

  const yearlyTotals = useMemo(() => {
    const agg = new Map<number, number>();
    for (const d of trends.data?.year_wise ?? []) {
      for (const y of d.yearly) {
        agg.set(y.year, (agg.get(y.year) ?? 0) + y.events);
      }
    }
    return [...agg.entries()].map(([year, events]) => ({ year, events })).sort((a, b) => a.year - b.year);
  }, [trends.data]);

  const seasonal = useMemo(
    () =>
      (trends.data?.seasonal_pattern ?? []).map((m) => ({
        month: MONTHS[m.month - 1] ?? String(m.month),
        events: m.events,
      })),
    [trends.data],
  );

  const districtTotals = useMemo(
    () =>
      (trends.data?.year_wise ?? [])
        .map((d) => ({
          district: d.district_name,
          events: d.total_events,
          trend: d.trend_2017_2024_vs_2010_2016,
        }))
        .sort((a, b) => b.events - a.events),
    [trends.data],
  );

  const statusCounts = useMemo(() => {
    const c: Record<string, number> = { pending: 0, verified: 0, rejected: 0, resolved: 0 };
    for (const r of reports.data ?? []) {
      if (r.status in c) c[r.status] += 1;
    }
    return Object.entries(c).map(([status, count]) => ({ status, count }));
  }, [reports.data]);

  const incidentStatusData = useMemo(() => {
    const bs = incidentStats.data?.by_status ?? {};
    return ["detected", "verified", "response_started", "resolved"].map((s) => ({
      status: s.replace(/_/g, " "),
      count: bs[s] ?? 0,
    }));
  }, [incidentStats.data]);

  const avgResolve = incidentStats.data?.avg_hours_to_resolve;

  return (
    <DashboardShell
      title="Analytics"
      subtitle="Flood trends, district comparison, alert history and response statistics"
      allowedRoles={["authority"]}
    >
      <CommandNav />

      <div className="grid gap-5 xl:grid-cols-2">
        {/* Flood trends */}
        <SectionCard title="Flood events per year" description="Recorded events across all districts (2010–2024)">
          {trends.loading && <Skeleton className="h-64" />}
          {trends.error && <p className="py-10 text-center text-sm text-red-600">{trends.error}</p>}
          {trends.data && yearlyTotals.length > 0 && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={yearlyTotals} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#64748b" interval={2} />
                  <YAxis tick={{ fontSize: 11 }} stroke="#64748b" allowDecimals={false} />
                  <Tooltip formatter={(v) => [`${v}`, "Events"]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="events" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </SectionCard>

        {/* Seasonal pattern */}
        <SectionCard title="Seasonal pattern" description="Events by month — monsoon concentration">
          {trends.loading && <Skeleton className="h-64" />}
          {trends.error && <p className="py-10 text-center text-sm text-red-600">{trends.error}</p>}
          {trends.data && seasonal.length > 0 && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={seasonal} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="#64748b" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#64748b" allowDecimals={false} />
                  <Tooltip formatter={(v) => [`${v}`, "Events"]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Line type="monotone" dataKey="events" stroke="#ea580c" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </SectionCard>
      </div>

      {/* District comparison */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="District comparison" description="Total recorded events per district">
          {trends.loading && <Skeleton className="h-64" />}
          {trends.error && <p className="py-10 text-center text-sm text-red-600">{trends.error}</p>}
          {trends.data && districtTotals.length > 0 && (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={districtTotals} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} stroke="#64748b" allowDecimals={false} />
                  <YAxis type="category" dataKey="district" tick={{ fontSize: 11 }} stroke="#64748b" width={90} />
                  <Tooltip formatter={(v) => [`${v}`, "Events"]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="events" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Trend direction per district" description="Mean events 2017–2024 vs 2010–2016">
          {trends.loading && <Skeleton className="h-40" />}
          {trends.data && districtTotals.length > 0 && (
            <ul className="divide-y divide-slate-100">
              {districtTotals.map((d) => (
                <li key={d.district} className="flex items-center justify-between py-2.5 text-sm">
                  <span className="font-medium text-navy-950">{d.district}</span>
                  <Badge
                    variant={d.trend === "increasing" ? "high" : d.trend === "decreasing" ? "low" : "medium"}
                  >
                    {d.trend}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
          {trends.data && <p className="mt-3 text-xs text-slate-500">{trends.data.note}</p>}
        </SectionCard>
      </div>

      {/* Alert history */}
      <section className="mt-5">
        <SectionCard title="Alert history" description="Issued warnings, most recent first (active and deactivated)">
          {alertHistory.loading && <Skeleton className="h-40" />}
          {alertHistory.error && <p className="py-6 text-center text-sm text-red-600">{alertHistory.error}</p>}
          {alertHistory.data && alertHistory.data.items.length === 0 && (
            <EmptyState title="No alerts issued" description="Alert history will appear here once warnings are issued." />
          )}
          {alertHistory.data && alertHistory.data.items.length > 0 && (
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-slate-200 text-left">
                    <th className="py-2 pr-4 font-semibold text-navy-950">Title</th>
                    <th className="py-2 pr-4 font-semibold text-navy-950">Severity</th>
                    <th className="py-2 pr-4 font-semibold text-navy-950">State</th>
                    <th className="py-2 font-semibold text-navy-950">Issued</th>
                  </tr>
                </thead>
                <tbody>
                  {alertHistory.data.items.map((a) => (
                    <tr key={a.id} className="border-b border-slate-100 last:border-0">
                      <td className="py-2 pr-4 font-medium text-navy-950">{a.title}</td>
                      <td className="py-2 pr-4">
                        <Badge
                          variant={
                            a.severity === "emergency" ? "emergency"
                            : a.severity === "warning" ? "warning"
                            : a.severity === "watch" ? "watch" : "info"
                          }
                        >
                          {a.severity}
                        </Badge>
                      </td>
                      <td className="py-2 pr-4">
                        <Badge variant={a.is_active ? "low" : "outline"}>
                          {a.is_active ? "active" : "deactivated"}
                        </Badge>
                      </td>
                      <td className="py-2 text-slate-600">
                        {new Date(a.issued_at).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </section>

      {/* Response statistics */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <SectionCard title="Incident response statistics" description="Lifecycle counts and resolution timing">
          {incidentStats.loading && <Skeleton className="h-56" />}
          {incidentStats.error && <p className="py-10 text-center text-sm text-red-600">{incidentStats.error}</p>}
          {incidentStats.data && (
            <>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-2xl font-bold text-navy-950">
                    {(incidents.data ?? []).filter((i) => i.status !== "resolved").length}
                  </p>
                  <p className="text-xs text-slate-500">Open incidents</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-2xl font-bold text-navy-950">
                    {avgResolve != null ? `${avgResolve.toFixed(1)}h` : "—"}
                  </p>
                  <p className="text-xs text-slate-500">Avg. time to resolve</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-2xl font-bold text-navy-950">{incidentStats.data.resolved_last_7d}</p>
                  <p className="text-xs text-slate-500">Resolved (7 days)</p>
                </div>
              </div>
              <div className="mt-4 h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={incidentStatusData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="status" tick={{ fontSize: 11 }} stroke="#64748b" />
                    <YAxis tick={{ fontSize: 11 }} stroke="#64748b" allowDecimals={false} />
                    <Tooltip formatter={(v) => [`${v}`, "Incidents"]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="count" fill="#b45309" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </SectionCard>

        <SectionCard title="Field report triage statistics" description="Citizen reports by triage state">
          {reports.loading && <Skeleton className="h-56" />}
          {reports.error && <p className="py-10 text-center text-sm text-red-600">{reports.error}</p>}
          {reports.data && (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusCounts} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="status" tick={{ fontSize: 11 }} stroke="#64748b" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#64748b" allowDecimals={false} />
                  <Tooltip formatter={(v) => [`${v}`, "Reports"]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="count" fill="#15803d" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </SectionCard>
      </div>

      {/* Current model predictions snapshot */}
      <section className="mt-5">
        <SectionCard title="Current model predictions" description="Latest district risk assessment snapshot">
          {summary.loading && <Skeleton className="h-32" />}
          {summary.data && summary.data.latest_predictions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {summary.data.latest_predictions.map((d) => (
                <span key={d.district_name} className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-xs">
                  <span className="font-semibold text-navy-950">{d.district_name}</span>
                  <Badge variant={d.risk_level === "HIGH" ? "high" : d.risk_level === "MEDIUM" ? "medium" : "low"}>
                    {formatProbability(d.probability)}
                  </Badge>
                </span>
              ))}
            </div>
          )}
        </SectionCard>
      </section>
    </DashboardShell>
  );
}
