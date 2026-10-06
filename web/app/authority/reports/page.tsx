"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CommandNav } from "@/components/authority/CommandNav";
import { PriorityBadge, ReportStatusBadge, SeverityBadge } from "@/components/authority/badges";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/api/hooks";
import { adminApi } from "@/lib/api/endpoints";
import type { CitizenReportOut, ReportPriority } from "@/lib/api/types";

const STATUS_FILTERS = ["", "pending", "verified", "rejected", "resolved"];
const CATEGORY_FILTERS = ["", "flood_water", "road_blockage", "rescue_request", "medical_emergency"];
const PRIORITIES: ReportPriority[] = ["low", "medium", "high", "urgent"];

function ReportCard({ report, onChange }: { report: CitizenReportOut; onChange: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [priority, setPriority] = useState<ReportPriority>(report.priority ?? "medium");
  const [error, setError] = useState<string | null>(null);

  async function triage(status: "verified" | "rejected" | "resolved") {
    setBusy(status);
    setError(null);
    try {
      await adminApi.verifyReport(report.id, { status, note: note.trim() || null, priority });
      setNote("");
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Triage failed.");
    } finally {
      setBusy(null);
    }
  }

  async function changePriority() {
    setBusy("priority");
    setError(null);
    try {
      await adminApi.verifyReport(report.id, { status: report.status, priority, note: null });
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Priority update failed.");
    } finally {
      setBusy(null);
    }
  }

  const priorityDirty = priority !== (report.priority ?? "medium");

  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <ReportStatusBadge status={report.status} />
          <PriorityBadge priority={report.priority ?? "medium"} />
          <SeverityBadge severity={report.severity ?? 3} />
          <span className="ml-auto text-xs text-slate-500">
            {new Date(report.created_at).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" })}
          </span>
        </div>
        <div>
          <p className="text-sm font-semibold text-navy-950">
            {report.district_name ?? "Unknown district"} · {report.category?.replace(/_/g, " ")}
          </p>
          <p className="mt-1 text-sm text-slate-700">{report.description}</p>
        </div>
        {error && <p className="text-xs text-red-600">{error}</p>}
        {report.status === "pending" && (
          <div className="space-y-2 rounded-lg bg-slate-50 p-3">
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor={`note-${report.id}`} className="text-xs">Verification note</Label>
                <Input
                  id={`note-${report.id}`}
                  placeholder="Evidence summary…"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="h-9"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor={`prio-${report.id}`} className="text-xs">Priority</Label>
                <select
                  id={`prio-${report.id}`}
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as ReportPriority)}
                  className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-2 text-sm"
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>{p.toUpperCase()}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="brand" disabled={busy !== null} onClick={() => triage("verified")}>
                {busy === "verified" && <Loader2 className="animate-spin" />} Verify
              </Button>
              <Button size="sm" variant="outline" disabled={busy !== null} onClick={() => triage("rejected")}>
                {busy === "rejected" && <Loader2 className="animate-spin" />} Reject
              </Button>
              <Button size="sm" variant="outline" disabled={busy !== null} onClick={() => triage("resolved")}>
                {busy === "resolved" && <Loader2 className="animate-spin" />} Resolve
              </Button>
            </div>
          </div>
        )}
        {report.status !== "pending" && (
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as ReportPriority)}
              className="h-9 rounded-md border border-slate-300 bg-white px-2 text-sm"
              aria-label={`Priority for report in ${report.district_name ?? "unknown district"}`}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p.toUpperCase()}</option>
              ))}
            </select>
            <Button size="sm" variant="outline" disabled={!priorityDirty || busy === "priority"} onClick={changePriority}>
              {busy === "priority" && <Loader2 className="animate-spin" />} Update priority
            </Button>
            {report.status === "verified" && (
              <Button size="sm" variant="outline" disabled={busy !== null} onClick={() => triage("resolved")}>
                {busy === "resolved" && <Loader2 className="animate-spin" />} Mark resolved
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ReportsPage() {
  const [statusFilter, setStatusFilter] = useState("pending");
  const [categoryFilter, setCategoryFilter] = useState("");
  const reports = useApi(
    () =>
      adminApi.reports({
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(categoryFilter ? { category: categoryFilter } : {}),
      }),
    [statusFilter, categoryFilter],
  );

  const list = reports.data ?? [];

  return (
    <DashboardShell
      title="Field Reports"
      subtitle="Verify, prioritise and resolve citizen flood reports"
      allowedRoles={["authority"]}
    >
      <CommandNav />

      <div className="mb-4 space-y-3">
        <div className="flex flex-wrap gap-2" aria-label="Status filter">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
                statusFilter === s
                  ? "border-navy-950 bg-navy-950 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:border-navy-600"
              }`}
            >
              {s === "" ? "All" : s}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2" aria-label="Category filter">
          {CATEGORY_FILTERS.map((c) => (
            <button
              key={c}
              onClick={() => setCategoryFilter(c)}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
                categoryFilter === c
                  ? "border-brand-600 bg-brand-600 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:border-brand-600"
              }`}
            >
              {c === "" ? "All categories" : c.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {reports.loading && <Skeleton className="h-64" />}
      {reports.error && <p className="text-sm text-red-600">Reports unavailable: {reports.error}</p>}
      {reports.data && list.length === 0 && (
        <EmptyState
          title="No reports"
          description="No citizen reports match these filters."
        />
      )}
      <div className="grid gap-4 xl:grid-cols-2">
        {list.map((r) => (
          <ReportCard key={r.id} report={r} onChange={reports.refetch} />
        ))}
      </div>
    </DashboardShell>
  );
}
