"use client";

import { Badge } from "@/components/ui/badge";
import type { IncidentStatus, ReportPriority } from "@/lib/api/types";

const INCIDENT_LABELS: Record<IncidentStatus, string> = {
  detected: "Detected",
  verified: "Verified",
  response_started: "Response started",
  resolved: "Resolved",
};

const INCIDENT_VARIANTS: Record<IncidentStatus, "high" | "warning" | "watch" | "low"> = {
  detected: "high",
  verified: "warning",
  response_started: "watch",
  resolved: "low",
};

export function IncidentStatusBadge({ status }: { status: IncidentStatus }) {
  return <Badge variant={INCIDENT_VARIANTS[status]}>{INCIDENT_LABELS[status]}</Badge>;
}

const PRIORITY_VARIANTS: Record<ReportPriority, "low" | "medium" | "warning" | "emergency"> = {
  low: "low",
  medium: "medium",
  high: "warning",
  urgent: "emergency",
};

export function PriorityBadge({ priority }: { priority: ReportPriority | string }) {
  const p = (priority as ReportPriority) in PRIORITY_VARIANTS ? (priority as ReportPriority) : "medium";
  return <Badge variant={PRIORITY_VARIANTS[p]}>{p.toUpperCase()}</Badge>;
}

const REPORT_VARIANTS: Record<string, "medium" | "low" | "high" | "info"> = {
  pending: "medium",
  verified: "info",
  rejected: "high",
  resolved: "low",
  dismissed: "high",
};

export function ReportStatusBadge({ status }: { status: string }) {
  return <Badge variant={REPORT_VARIANTS[status] ?? "outline"}>{status}</Badge>;
}

export function SeverityBadge({ severity }: { severity: number }) {
  const variant = severity >= 4 ? "emergency" : severity === 3 ? "warning" : severity === 2 ? "watch" : "low";
  return <Badge variant={variant}>S{severity}</Badge>;
}
