"use client";

import { useMemo, useState, type FormEvent } from "react";
import { Plus, Loader2, StickyNote, ArrowRight, History } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CommandNav } from "@/components/authority/CommandNav";
import { IncidentStatusBadge, SeverityBadge } from "@/components/authority/badges";
import { IncidentTimeline, incidentToTimeline } from "@/components/IncidentTimeline";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useApi } from "@/lib/api/hooks";
import { gisApi, incidentsApi } from "@/lib/api/endpoints";
import type { IncidentOut, IncidentStatus } from "@/lib/api/types";

const WORKFLOW: IncidentStatus[] = ["detected", "verified", "response_started", "resolved"];
const WORKFLOW_LABELS: Record<IncidentStatus, string> = {
  detected: "Detected",
  verified: "Mark verified",
  response_started: "Start response",
  resolved: "Mark resolved",
};

const STATUS_FILTERS: Array<{ value: string; label: string }> = [
  { value: "", label: "All" },
  { value: "detected", label: "Detected" },
  { value: "verified", label: "Verified" },
  { value: "response_started", label: "In response" },
  { value: "resolved", label: "Resolved" },
];

function CreateIncidentForm({ onCreated }: { onCreated: () => void }) {
  const districts = useApi(() => gisApi.districts());
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [district, setDistrict] = useState("");
  const [severity, setSeverity] = useState(3);
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    try {
      await incidentsApi.create({
        title: title.trim(),
        description: description.trim() || null,
        district_name: district || null,
        severity,
      });
      setOpen(false);
      setTitle("");
      setDistrict("");
      setDescription("");
      setSeverity(3);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the incident.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <Button variant="brand" onClick={() => setOpen(true)}>
        <Plus /> New incident
      </Button>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Raise incident</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div className="space-y-2">
            <Label htmlFor="inc-title">Title</Label>
            <Input
              id="inc-title"
              required
              minLength={3}
              placeholder="e.g. Embankment breach near Mehar"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="inc-district">District</Label>
              <select
                id="inc-district"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
              >
                <option value="">No district</option>
                {names.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="inc-severity">Severity (1–5)</Label>
              <select
                id="inc-severity"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm"
              >
                {[1, 2, 3, 4, 5].map((v) => (
                  <option key={v} value={v}>
                    {v} — {["", "Minor", "Moderate", "Major", "Severe", "Catastrophic"][v]}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="inc-desc">Description</Label>
            <textarea
              id="inc-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Situation on the ground…"
              className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400"
            />
          </div>
          <div className="flex gap-2">
            <Button type="submit" variant="brand" disabled={busy}>
              {busy && <Loader2 className="animate-spin" />} Raise incident
            </Button>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function IncidentDetail({ incident, onChange }: { incident: IncidentOut; onChange: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  const currentIdx = WORKFLOW.indexOf(incident.status);
  const nextStatus: IncidentStatus | null =
    currentIdx < WORKFLOW.length - 1 ? WORKFLOW[currentIdx + 1] : null;

  async function advance() {
    if (!nextStatus) return;
    setBusy(nextStatus);
    setError(null);
    try {
      await incidentsApi.updateStatus(incident.id, nextStatus);
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed.");
    } finally {
      setBusy(null);
    }
  }

  async function addNote(e: FormEvent) {
    e.preventDefault();
    if (!note.trim()) return;
    setBusy("note");
    setError(null);
    try {
      await incidentsApi.addNote(incident.id, note.trim());
      setNote("");
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add the note.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card>
      <CardContent className="space-y-5 p-5">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <IncidentStatusBadge status={incident.status} />
          <SeverityBadge severity={incident.severity} />
        </div>
        <div>
          <h3 className="text-lg font-bold text-navy-950">{incident.title}</h3>
          <p className="mt-1 text-sm text-slate-600">
            {incident.district_name ?? "No district"} · raised{" "}
            {new Date(incident.created_at).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" })}
            {incident.resolved_at &&
              ` · resolved ${new Date(incident.resolved_at).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" })}`}
          </p>
          {incident.description && <p className="mt-3 text-sm text-slate-700">{incident.description}</p>}
        </div>

        {/* Workflow stepper */}
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Workflow</p>
          <div className="flex flex-wrap items-center gap-1">
            {WORKFLOW.map((s, i) => (
              <span key={s} className="flex items-center gap-1">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                    i < currentIdx
                      ? "bg-emerald-100 text-emerald-800"
                      : i === currentIdx
                        ? "bg-navy-950 text-white"
                        : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {["Detected", "Verified", "Response started", "Resolved"][i]}
                </span>
                {i < WORKFLOW.length - 1 && <ArrowRight className="h-3 w-3 text-slate-300" />}
              </span>
            ))}
          </div>
          {nextStatus && (
            <Button variant="brand" size="sm" className="mt-3" disabled={busy === nextStatus} onClick={advance}>
              {busy === nextStatus && <Loader2 className="animate-spin" />}
              {WORKFLOW_LABELS[nextStatus]}
            </Button>
          )}
        </div>

        {/* Incident timeline */}
        <div>
          <p className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <History className="h-3.5 w-3.5" /> Incident timeline
          </p>
          <IncidentTimeline events={incidentToTimeline(incident)} />
        </div>

        {/* Notes timeline */}
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <StickyNote className="h-3.5 w-3.5" /> Notes ({incident.notes.length})
          </p>
          {incident.notes.length === 0 && (
            <p className="text-sm text-slate-400">No notes yet.</p>
          )}
          <ul className="space-y-2">
            {incident.notes.map((n) => (
              <li key={n.id} className="rounded-lg bg-slate-50 p-3 text-sm">
                <p className="text-slate-700">{n.note}</p>
                <p className="mt-1 text-xs text-slate-400">
                  {new Date(n.created_at).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" })}
                </p>
              </li>
            ))}
          </ul>
          <form onSubmit={addNote} className="mt-3 flex gap-2">
            <Input
              placeholder="Add an operational note…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <Button type="submit" variant="outline" size="sm" disabled={busy === "note" || !note.trim()}>
              {busy === "note" && <Loader2 className="animate-spin" />} Add
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}

export default function IncidentsPage() {
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const incidents = useApi(() => incidentsApi.list(filter ? { status: filter } : undefined), [filter]);
  const selected = useApi(() => (selectedId ? incidentsApi.get(selectedId) : Promise.resolve(null)), [selectedId]);

  const list = incidents.data ?? [];

  return (
    <DashboardShell
      title="Incident Management"
      subtitle="Detected → Verified → Response started → Resolved"
      allowedRoles={["authority"]}
    >
      <CommandNav />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => {
                setFilter(f.value);
                setSelectedId(null);
              }}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
                filter === f.value
                  ? "border-navy-950 bg-navy-950 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:border-navy-600"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <CreateIncidentForm
          onCreated={() => {
            incidents.refetch();
          }}
        />
      </div>

      {incidents.loading && <Skeleton className="h-64" />}
      {incidents.error && <p className="text-sm text-red-600">Incidents unavailable: {incidents.error}</p>}
      {incidents.data && list.length === 0 && (
        <EmptyState
          title="No incidents"
          description={
            filter
              ? "No incidents in this state. Raise one with the button above."
              : "Raise the first incident with the button above, or escalate one from an alert or field report."
          }
        />
      )}

      {list.length > 0 && (
        <div className="grid gap-5 xl:grid-cols-2">
          <div className="space-y-2">
            {list.map((i) => (
              <button
                key={i.id}
                onClick={() => setSelectedId(i.id)}
                className={`w-full rounded-xl border bg-white p-4 text-left transition-colors ${
                  selectedId === i.id ? "border-navy-600 ring-1 ring-navy-600" : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-navy-950">{i.title}</p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {i.district_name ?? "No district"} ·{" "}
                      {new Date(i.created_at).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" })}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <SeverityBadge severity={i.severity} />
                    <IncidentStatusBadge status={i.status} />
                  </div>
                </div>
              </button>
            ))}
          </div>
          <div>
            {selectedId === null && (
              <EmptyState title="Select an incident" description="Choose an incident to review its workflow and notes." />
            )}
            {selected.loading && <Skeleton className="h-64" />}
            {selected.data && (
              <IncidentDetail
                incident={selected.data}
                onChange={() => {
                  selected.refetch();
                  incidents.refetch();
                }}
              />
            )}
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
