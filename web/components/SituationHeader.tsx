"use client";

import Link from "next/link";
import {
  BellRing,
  ChevronRight,
  Clock,
  MapPinned,
  Radio,
  ShieldCheck,
  Siren,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { timeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface SituationHeaderData {
  /** Alerts currently in force */
  activeAlerts: number;
  /** Of those, how many are emergency severity */
  emergencyAlerts: number;
  /** Districts currently at HIGH risk */
  highRiskDistricts: number;
  /** Names of the high-risk districts (for the link hint) */
  highRiskNames: string[];
  /** ISO timestamp of the underlying assessment cycle */
  generatedAt: string | null;
}

export type SituationLevel = "emergency" | "watch" | "calm";

const LEVEL_META: Record<
  SituationLevel,
  { label: string; dot: string; ring: string; text: string; icon: typeof Siren }
> = {
  emergency: {
    label: "Emergency",
    dot: "bg-red-500",
    ring: "bg-red-500/30",
    text: "text-red-400",
    icon: Siren,
  },
  watch: {
    label: "Watch",
    dot: "bg-amber-400",
    ring: "bg-amber-400/30",
    text: "text-amber-300",
    icon: ShieldCheck,
  },
  calm: {
    label: "Calm",
    dot: "bg-emerald-400",
    ring: "bg-emerald-400/30",
    text: "text-emerald-300",
    icon: ShieldCheck,
  },
};

export function situationLevel(d: SituationHeaderData): SituationLevel {
  if (d.emergencyAlerts > 0 || d.highRiskDistricts > 0) return "emergency";
  if (d.activeAlerts > 0) return "watch";
  return "calm";
}

/**
 * Operational situation header — the command-centre panel at the top of a
 * dashboard. Dark navy, visually prominent: live status, active alerts,
 * high-risk districts, and the age of the underlying data.
 *
 * Purely presentational: pass data mapped from any live endpoint
 * (/public/situation for citizens, /dashboard/summary for command staff).
 */
export function SituationHeader({
  data,
  loading = false,
  alertsHref = "/dashboard#alerts",
  mapHref = "/map",
}: {
  data: SituationHeaderData | null;
  loading?: boolean;
  alertsHref?: string;
  mapHref?: string;
}) {
  if (loading || !data) {
    return <Skeleton className="h-44 w-full rounded-2xl bg-navy-900/40" />;
  }

  const level = situationLevel(data);
  const meta = LEVEL_META[level];
  const StatusIcon = meta.icon;

  return (
    <section
      aria-label="Live flood situation"
      className="animate-fade-in-up relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 p-6 text-white shadow-xl sm:p-8"
    >
      {/* Decorative radar sweep */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-brand-600/10 blur-2xl"
      />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-white/70">
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={cn(
                    "absolute inline-flex h-full w-full animate-ping rounded-full opacity-60",
                    meta.dot,
                  )}
                />
                <span
                  className={cn("relative inline-flex h-2.5 w-2.5 rounded-full", meta.dot)}
                />
              </span>
              <Radio className="h-3.5 w-3.5" />
              Live flood situation
            </p>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl">
              Sindh Province
            </h2>
          </div>
          <div
            className={cn(
              "flex items-center gap-3 rounded-xl border border-white/15 bg-white/5 px-4 py-3",
            )}
          >
            <span className="relative flex h-4 w-4">
              <span
                className={cn("absolute h-full w-full animate-ping rounded-full opacity-50", meta.ring)}
              />
              <span className={cn("relative h-4 w-4 rounded-full", meta.dot)} />
            </span>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-white/60">
                Current status
              </p>
              <p className={cn("flex items-center gap-1.5 text-xl font-extrabold", meta.text)}>
                <StatusIcon className="h-5 w-5" />
                {meta.label}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-white/60">
              <BellRing className="h-3.5 w-3.5" /> Active alerts
            </p>
            <p className="mt-1 text-3xl font-extrabold">{data.activeAlerts}</p>
          </div>
          <Link
            href={mapHref}
            className="group rounded-xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10"
          >
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-white/60">
              <MapPinned className="h-3.5 w-3.5" /> High-risk districts
            </p>
            <p className="mt-1 flex items-center gap-1 text-3xl font-extrabold">
              {data.highRiskDistricts}
              <ChevronRight className="h-5 w-5 text-white/40 transition-transform group-hover:translate-x-1" />
            </p>
          </Link>
          <div className="rounded-xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10">
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-white/60">
              <Clock className="h-3.5 w-3.5" /> Last updated
            </p>
            <p className="mt-1 text-lg font-bold leading-9">
              {timeAgo(data.generatedAt)}
            </p>
          </div>
          <Link
            href={alertsHref}
            className="group flex items-center justify-between rounded-xl bg-brand-600 p-4 font-bold transition-colors hover:bg-brand-500"
          >
            <span>
              <span className="block text-[11px] font-semibold uppercase tracking-wider text-white/80">
                Operations
              </span>
              <span className="text-lg">Alert centre</span>
            </span>
            <ChevronRight className="h-6 w-6 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </section>
  );
}
