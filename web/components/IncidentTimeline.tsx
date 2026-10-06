"use client";

import { CheckCircle2, Circle, FileText, Flag } from "lucide-react";
import type { IncidentOut } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export interface TimelineEvent {
  date: string;
  title: string;
  description?: string;
  kind: "start" | "note" | "resolved" | "update";
}

const KIND_STYLE: Record<TimelineEvent["kind"], { dot: string; icon: typeof Circle }> = {
  start: { dot: "bg-red-600", icon: Flag },
  note: { dot: "bg-navy-600", icon: FileText },
  update: { dot: "bg-amber-500", icon: Circle },
  resolved: { dot: "bg-emerald-600", icon: CheckCircle2 },
};

function formatDay(iso: string): string {
  try {
    const d = new Date(iso);
    const day = d.toLocaleDateString("en-PK", { day: "numeric", month: "short" });
    const time = d.toLocaleTimeString("en-PK", { hour: "2-digit", minute: "2-digit" });
    return `${day} · ${time}`;
  } catch {
    return iso;
  }
}

/**
 * Vertical event timeline — every major alert/incident gets one.
 * Purely presentational; feed it events derived from live incident,
 * alert, or report records.
 */
export function IncidentTimeline({ events }: { events: TimelineEvent[] }) {
  const sorted = [...events].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  );
  return (
    <ol className="relative space-y-6 border-l-2 border-slate-200 pl-0">
      {sorted.map((e, i) => {
        const meta = KIND_STYLE[e.kind];
        const Icon = meta.icon;
        return (
          <li key={`${e.date}-${i}`} className="relative pl-10">
            <span
              className={cn(
                "absolute -left-[13px] top-0 flex h-6 w-6 items-center justify-center rounded-full text-white",
                meta.dot,
              )}
            >
              <Icon className="h-3.5 w-3.5" />
            </span>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {formatDay(e.date)}
            </p>
            <p className="mt-0.5 font-semibold text-navy-950">{e.title}</p>
            {e.description && (
              <p className="mt-0.5 text-sm text-slate-600">{e.description}</p>
            )}
          </li>
        );
      })}
    </ol>
  );
}

const SOURCE_LABEL: Record<string, string> = {
  alert: "Early-warning alert triggered this incident",
  report: "Citizen field report opened this incident",
  manual: "Incident logged by command staff",
};

const STATUS_LABEL: Record<string, string> = {
  detected: "Detected",
  verified: "Verified by command staff",
  response_started: "Response started",
  resolved: "Resolved",
};

/** Build timeline events from a live IncidentOut record. */
export function incidentToTimeline(incident: IncidentOut): TimelineEvent[] {
  const events: TimelineEvent[] = [
    {
      date: incident.created_at,
      title: SOURCE_LABEL[incident.source] ?? "Incident opened",
      description: incident.title,
      kind: "start",
    },
  ];
  for (const n of incident.notes ?? []) {
    events.push({
      date: n.created_at,
      title: "Situation note added",
      description: n.note,
      kind: "note",
    });
  }
  if (incident.status !== "detected") {
    events.push({
      date: incident.updated_at,
      title: `Status: ${STATUS_LABEL[incident.status] ?? incident.status}`,
      kind: incident.status === "resolved" ? "resolved" : "update",
    });
  }
  if (incident.resolved_at && incident.status === "resolved") {
    // resolved_at marks the terminal milestone distinctly from updated_at
    events.push({
      date: incident.resolved_at,
      title: "Incident closed — area stood down",
      kind: "resolved",
    });
  }
  return events;
}
