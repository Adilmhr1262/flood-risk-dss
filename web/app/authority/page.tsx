"use client";

import { useMemo, useState, type FormEvent } from "react";
import {
  TriangleAlert,
  Megaphone,
  ClipboardList,
  Loader2,
  Ban,
  Siren,
  CloudRain,
} from "lucide-react";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CommandNav } from "@/components/authority/CommandNav";
import { IncidentStatusBadge, ReportStatusBadge } from "@/components/authority/badges";
import { StatCard } from "@/components/StatCard";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useApi } from "@/lib/api/hooks";
import { formatProbability } from "@/lib/format";
import { SituationHeader } from "@/components/SituationHeader";
import {
  adminApi,
  alertsApi,
  decisionSupportApi,
  gisApi,
  incidentsApi,
  weatherApi,
} from "@/lib/api/endpoints";
import type { AlertSeverity } from "@/lib/api/types";

function IssueAlertForm({ onIssued }: { onIssued: () => void }) {
  const districts = useApi(() => gisApi.districts());
  const [district, setDistrict] = useState("");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState<AlertSeverity>("watch");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const names = useMemo(
    () =>
      (districts.data?.features ?? [])
        .map((f) => String(f.properties?.district_name ?? ""))
        .filter(Boolean)
        .sort(),
    [districts.data],
  );

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      await alertsApi.create({
        district_name: district,
        title: title.trim(),
        message: message.trim(),
        severity,
      });
      setDone(true);
      setTitle("");
      setMessage("");
      onIssued();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not issue the alert.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Issue new alert</CardTitle>
        <CardDescription>Broadcast a severity-graded warning for a district</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <TriangleAlert />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {done && (
            <Alert variant="info">
              <AlertDescription>Alert issued and now active.</AlertDescription>
            </Alert>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="district">District</Label>
              <select
                id="district"
                required
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-600"
              >
                <option value="">Select district…</option>
                {names.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="severity">Severity</Label>
              <select
                id="severity"
                value={severity}
                onChange={(e) => setSeverity(e.target.value as AlertSeverity)}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-600"
              >
                <option value="info">Info / advisory</option>
                <option value="watch">Watch</option>
                <option value="warning">Warning</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              required
              minLength={2}
              placeholder="e.g. Flood warning: Dadu district"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <textarea
              id="message"
              required
              minLength={2}
              rows={3}
              placeholder="What should residents do?"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-600"
            />
          </div>
          <Button type="submit" variant="alert" disabled={busy}>
            {busy && <Loader2 className="animate-spin" />}
            <Megaphone /> {busy ? "Issuing…" : "Issue alert"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function AuthorityCommandPage() {
  const summary = useApi(() => decisionSupportApi.summary());
  const alerts = useApi(() => alertsApi.list(1, 20, true));
  const incidents = useApi(() => incidentsApi.list());
  const reports = useApi(() => adminApi.reports({ status: "pending" }));
  const weather = useApi(() => weatherApi.latest());
  const [deactivating, setDeactivating] = useState<string | null>(null);

  async function deactivate(id: string) {
    setDeactivating(id);
    try {
      await alertsApi.deactivate(id);
      alerts.refetch();
      summary.refetch();
    } finally {
      setDeactivating(null);
    }
  }

  const s = summary.data;
  const openIncidents = (incidents.data ?? []).filter((i) => i.status !== "resolved");
  const pendingReports = reports.data ?? [];
  const wettest = (weather.data ?? [])
    .filter((w) => w.rainfall_mm != null)
    .sort((a, b) => (b.rainfall_mm ?? 0) - (a.rainfall_mm ?? 0))
    .slice(0, 6);

  return (
    <DashboardShell
      title="Command Overview"
      subtitle="Live operational picture for disaster management officials"
      allowedRoles={["authority"]}
    >
      <CommandNav />

      {/* Live flood situation header */}
      <SituationHeader
        data={
          s
            ? {
                activeAlerts: s.active_alerts.length,
                emergencyAlerts: s.active_alerts.filter(
                  (a) => a.severity === "emergency",
                ).length,
                highRiskDistricts: s.high_risk_districts.length,
                highRiskNames: s.high_risk_districts.map(
                  (d) => d.district_name,
                ),
                generatedAt: null,
              }
            : null
        }
        loading={summary.loading}
        alertsHref="/authority#alerts"
        mapHref="/authority/map"
      />

      {/* Key figures */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Active alerts"
          value={alerts.data?.items.length ?? "—"}
          hint="warnings currently in force — click to open alert centre"
          icon={Megaphone}
          accent="orange"
          loading={alerts.loading}
          href="/authority#alerts"
        />
        <StatCard
          label="Open incidents"
          value={incidents.data ? openIncidents.length : "—"}
          hint="detected / verified / in response — click to manage"
          icon={Siren}
          accent="red"
          loading={incidents.loading}
          href="/authority/incidents"
        />
        <StatCard
          label="High-risk districts"
          value={s?.high_risk_districts.length ?? "—"}
          hint="districts at HIGH risk now — click to open command map"
          icon={TriangleAlert}
          accent="navy"
          loading={summary.loading}
          href="/authority/map"
        />
        <StatCard
          label="Pending field reports"
          value={reports.data ? pendingReports.length : "—"}
          hint="awaiting authority triage — click to review"
          icon={ClipboardList}
          accent="emerald"
          loading={reports.loading}
          href="/authority/reports"
        />
      </div>

      {/* Active alerts + issue form */}
      <div className="mt-8 grid gap-5 xl:grid-cols-2">
        <section id="alerts" className="scroll-mt-28">
          <h2 className="mb-3 text-lg font-semibold text-navy-950">Active alerts</h2>
          {alerts.loading && <Skeleton className="h-40" />}
          {alerts.error && (
            <p className="text-sm text-red-600">Alerts unavailable: {alerts.error}</p>
          )}
          {alerts.data && alerts.data.items.length === 0 && (
            <EmptyState
              title="No active alerts"
              description="Issue the first alert with the form."
            />
          )}
          {alerts.data && alerts.data.items.length > 0 && (
            <Card>
              <CardContent className="p-0">
                <ul className="divide-y divide-slate-100">
                  {alerts.data.items.map((a) => (
                    <li key={a.id} className="flex items-start justify-between gap-3 p-4">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-navy-950">{a.title}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {new Date(a.issued_at).toLocaleString("en-PK", {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        <Badge
                          variant={
                            a.severity === "emergency"
                              ? "emergency"
                              : a.severity === "warning"
                                ? "warning"
                                : a.severity === "watch"
                                  ? "watch"
                                  : "info"
                          }
                        >
                          {a.severity}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={deactivating === a.id}
                          onClick={() => deactivate(a.id)}
                        >
                          {deactivating === a.id ? <Loader2 className="animate-spin" /> : <Ban />}
                          <span className="hidden sm:inline">Deactivate</span>
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </section>
        <IssueAlertForm
          onIssued={() => {
            alerts.refetch();
            summary.refetch();
          }}
        />
      </div>

      {/* High-risk districts + latest predictions */}
      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold text-navy-950">
          High-risk districts & latest predictions
        </h2>
        {summary.loading && <Skeleton className="h-48" />}
        {summary.error && (
          <p className="text-sm text-red-600">Decision support unavailable: {summary.error}</p>
        )}
        {s && s.latest_predictions.length === 0 && (
          <EmptyState
            title="No predictions yet"
            description="District predictions will appear here once the prediction service has run."
          />
        )}
        {s && s.latest_predictions.length > 0 && (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-navy-950 text-left text-white">
                      <th className="px-4 py-3 font-semibold">District</th>
                      <th className="px-4 py-3 font-semibold">Risk</th>
                      <th className="px-4 py-3 font-semibold">Probability</th>
                      <th className="px-4 py-3 font-semibold">Model</th>
                      <th className="px-4 py-3 font-semibold">Top factors</th>
                    </tr>
                  </thead>
                  <tbody>
                    {s.latest_predictions.slice(0, 8).map((d) => (
                      <tr key={d.district_name} className="border-b border-slate-100 last:border-0">
                        <td className="px-4 py-3 font-medium text-navy-950">{d.district_name}</td>
                        <td className="px-4 py-3">
                          <Badge variant={d.risk_level === "HIGH" ? "high" : d.risk_level === "MEDIUM" ? "medium" : "low"}>
                            {d.risk_level}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{formatProbability(d.probability)}</td>
                        <td className="px-4 py-3 text-slate-600">{d.model_version}</td>
                        <td className="px-4 py-3 text-slate-600">
                          {(d.top_factors ?? []).slice(0, 2).map((f) => f.feature).join("; ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Weather status + incidents + reports */}
      <div className="mt-8 grid gap-5 xl:grid-cols-3">
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-navy-950">
            <CloudRain className="h-5 w-5" /> Weather status
          </h2>
          {weather.loading && <Skeleton className="h-40" />}
          {weather.error && <p className="text-sm text-red-600">Weather unavailable: {weather.error}</p>}
          {weather.data && weather.data.length === 0 && (
            <EmptyState title="No observations" description="Weather ingestion has not recorded any observations yet." />
          )}
          {wettest.length > 0 && (
            <Card>
              <CardContent className="p-0">
                <ul className="divide-y divide-slate-100">
                  {wettest.map((w) => (
                    <li key={w.district_name} className="flex items-center justify-between p-3 text-sm">
                      <span className="font-medium text-navy-950">{w.district_name}</span>
                      <span className="text-slate-600">
                        {w.rainfall_mm?.toFixed(1)} mm
                        {w.temperature_c != null && ` · ${w.temperature_c.toFixed(0)}°C`}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
          <p className="mt-2 text-xs text-slate-500">
            Latest observation per district, wettest first. Full feed in Analytics.
          </p>
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-navy-950">Open incidents</h2>
            <Link href="/authority/incidents" className="text-xs font-semibold text-navy-700 hover:underline">
              Manage →
            </Link>
          </div>
          {incidents.loading && <Skeleton className="h-40" />}
          {incidents.data && openIncidents.length === 0 && (
            <EmptyState title="No open incidents" description="Raise one from the Incidents page." />
          )}
          {openIncidents.length > 0 && (
            <Card>
              <CardContent className="p-0">
                <ul className="divide-y divide-slate-100">
                  {openIncidents.slice(0, 6).map((i) => (
                    <li key={i.id} className="flex items-center justify-between gap-2 p-3 text-sm">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-navy-950">{i.title}</p>
                        <p className="text-xs text-slate-500">{i.district_name ?? "No district"}</p>
                      </div>
                      <IncidentStatusBadge status={i.status} />
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-navy-950">Reports awaiting triage</h2>
            <Link href="/authority/reports" className="text-xs font-semibold text-navy-700 hover:underline">
              Triage →
            </Link>
          </div>
          {reports.loading && <Skeleton className="h-40" />}
          {reports.data && pendingReports.length === 0 && (
            <EmptyState title="Queue clear" description="No pending citizen reports." />
          )}
          {pendingReports.length > 0 && (
            <Card>
              <CardContent className="p-0">
                <ul className="divide-y divide-slate-100">
                  {pendingReports.slice(0, 6).map((r) => (
                    <li key={r.id} className="flex items-center justify-between gap-2 p-3 text-sm">
                      <div className="min-w-0">
                        <p className="truncate font-medium text-navy-950">{r.district_name ?? "Unknown district"}</p>
                        <p className="truncate text-xs text-slate-500">
                          {r.category?.replace(/_/g, " ")} · {(r.description ?? "").slice(0, 60)}
                        </p>
                      </div>
                      <ReportStatusBadge status={r.status} />
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </DashboardShell>
  );
}
