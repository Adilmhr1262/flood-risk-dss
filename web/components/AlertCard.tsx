import Link from "next/link";
import {
  BellRing,
  Clock,
  Gauge,
  Map as MapIcon,
  Siren,
  Eye,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AlertOut } from "@/lib/api/types";
import { formatProbability, timeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

type Severity = "info" | "watch" | "warning" | "emergency";

const SEVERITY_META: Record<
  Severity,
  {
    label: string;
    icon: typeof BellRing;
    banner: string;
    band: string;
    chip: string;
    ring: string;
  }
> = {
  emergency: {
    label: "Flood Emergency",
    icon: Siren,
    banner: "bg-red-700",
    band: "border-l-red-700",
    chip: "bg-red-100 text-red-800",
    ring: "bg-red-100 text-red-700",
  },
  warning: {
    label: "Flood Warning",
    icon: BellRing,
    banner: "bg-orange-600",
    band: "border-l-orange-600",
    chip: "bg-orange-100 text-orange-800",
    ring: "bg-orange-100 text-orange-700",
  },
  watch: {
    label: "Flood Watch",
    icon: Eye,
    banner: "bg-amber-500",
    band: "border-l-amber-500",
    chip: "bg-amber-100 text-amber-800",
    ring: "bg-amber-100 text-amber-700",
  },
  info: {
    label: "Advisory",
    icon: BellRing,
    banner: "bg-sky-600",
    band: "border-l-sky-600",
    chip: "bg-sky-100 text-sky-800",
    ring: "bg-sky-100 text-sky-700",
  },
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-PK", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

interface AlertCardProps {
  alert: AlertOut;
  /** Where the "Open incident" action leads; omitted for public viewers. */
  incidentHref?: string;
}

/**
 * Emergency alert card rendered from a real GET /alerts response.
 *
 * Visual states: Emergency / Warning / Watch / Advisory — a coloured
 * severity banner, district + timing metadata, modelled probability, and
 * action buttons that route to the map or the incident workflow.
 */
export function AlertCard({ alert, incidentHref }: AlertCardProps) {
  const sev = (SEVERITY_META[alert.severity as Severity] ??
    SEVERITY_META.info) as (typeof SEVERITY_META)[Severity];
  const Icon = sev.icon;

  return (
    <Card
      className={cn(
        "animate-fade-in-up overflow-hidden border-l-4 transition-shadow hover:shadow-lg",
        sev.band,
      )}
    >
      {/* Severity banner */}
      <div className={cn("flex items-center gap-2 px-5 py-2 text-white", sev.banner)}>
        <Icon className="h-4 w-4" />
        <span className="text-xs font-bold uppercase tracking-widest">
          {sev.label}
        </span>
        <span className="ml-auto flex items-center gap-1 text-[11px] text-white/85">
          <Clock className="h-3 w-3" />
          {timeAgo(alert.issued_at)}
        </span>
      </div>

      <CardContent className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="font-bold text-navy-950">{alert.title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              {alert.message}
            </p>
          </div>
          <Badge variant="outline" className={cn("shrink-0", sev.chip)}>
            {alert.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>

        <div className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
          <div className="rounded-lg bg-slate-50 px-3 py-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Issued
            </p>
            <p className="mt-0.5 font-semibold text-navy-950">
              {formatDate(alert.issued_at)}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 px-3 py-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Modelled probability
            </p>
            <p className="mt-0.5 flex items-center gap-1 font-semibold text-navy-950">
              <Gauge className="h-3.5 w-3.5 text-slate-400" />
              {formatProbability(alert.probability)}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 px-3 py-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Status
            </p>
            <p className="mt-0.5 font-semibold text-navy-950">
              {alert.is_active ? "Monitoring" : "Closed"}
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/map"
            className="inline-flex items-center gap-1.5 rounded-lg bg-navy-950 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-navy-800"
          >
            <MapIcon className="h-4 w-4" /> View map
          </Link>
          {incidentHref && (
            <Link
              href={incidentHref}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-navy-950 transition-colors hover:border-navy-700 hover:text-navy-700"
            >
              Open incident <ChevronRight className="h-4 w-4" />
            </Link>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
