"use client";

import { useMemo, useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/EmptyState";
import { useApi } from "@/lib/api/hooks";
import { publicApi, type GeoJSONFeatureCollection } from "@/lib/api/public";
import {
  CalendarDays,
  Droplets,
  History,
  MapPin,
  RotateCcw,
  Users,
} from "lucide-react";

interface FloodEvent {
  event_id: string;
  district_name: string;
  province: string | null;
  event_date: string;
  year: number;
  severity: number;
  severity_label: string;
  rainfall_mm: number | null;
  affected_population: number | null;
  damage_description: string | null;
  source: string | null;
}

const SEVERITY_STYLES: Record<string, string> = {
  severe: "bg-red-100 text-red-800 border-red-200",
  moderate: "bg-amber-100 text-amber-800 border-amber-200",
  minor: "bg-sky-100 text-sky-800 border-sky-200",
  low: "bg-emerald-100 text-emerald-800 border-emerald-200",
};

function severityStyle(label: string): string {
  const key = label.toLowerCase();
  return (
    SEVERITY_STYLES[key] ?? "bg-slate-100 text-slate-700 border-slate-200"
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatNumber(n: number | null): string {
  if (n === null || n === undefined) return "Not recorded";
  return n.toLocaleString("en-PK");
}

const selectClass =
  "h-9 rounded-lg border border-slate-300 bg-white px-2 text-xs text-navy-950 focus:border-brand-500 focus:outline-none";

/**
 * Public flood history explorer — every recorded flood event (2010–2024)
 * with district, year, and severity filters. Read-only view over the
 * verified /public/historical-floods dataset; no data is invented here.
 */
export default function HistoryPage() {
  const floods = useApi<GeoJSONFeatureCollection>(() =>
    publicApi.historicalFloods(),
  );
  const districtList = useApi(() => publicApi.districts());

  const [district, setDistrict] = useState("all");
  const [year, setYear] = useState("all");
  const [severity, setSeverity] = useState("all");

  const events: FloodEvent[] = useMemo(
    () =>
      (floods.data?.features ?? []).map(
        (f) => f.properties as unknown as FloodEvent,
      ),
    [floods.data],
  );

  const years = useMemo(
    () =>
      Array.from(new Set(events.map((e) => e.year))).sort((a, b) => b - a),
    [events],
  );
  const severities = useMemo(
    () => Array.from(new Set(events.map((e) => e.severity_label))).sort(),
    [events],
  );
  const districts = useMemo(
    () =>
      (districtList.data?.districts ?? [])
        .map((d) => d.district_name)
        .sort(),
    [districtList.data],
  );

  const filtered = useMemo(
    () =>
      events
        .filter(
          (e) =>
            (district === "all" || e.district_name === district) &&
            (year === "all" || e.year === Number(year)) &&
            (severity === "all" || e.severity_label === severity),
        )
        .sort((a, b) => b.event_date.localeCompare(a.event_date)),
    [events, district, year, severity],
  );

  const stats = useMemo(() => {
    const affected = filtered.reduce(
      (sum, e) => sum + (e.affected_population ?? 0),
      0,
    );
    const byYear = new Map<number, number>();
    for (const e of filtered) byYear.set(e.year, (byYear.get(e.year) ?? 0) + 1);
    let worstYear: number | null = null;
    let worstCount = 0;
    for (const [y, n] of byYear) {
      if (n > worstCount) {
        worstCount = n;
        worstYear = y;
      }
    }
    return {
      events: filtered.length,
      affected,
      districts: new Set(filtered.map((e) => e.district_name)).size,
      worstYear,
    };
  }, [filtered]);

  const loading = floods.loading || districtList.loading;
  const error = floods.error ?? districtList.error;
  const refetch = () => {
    floods.refetch();
    districtList.refetch();
  };
  const hasFilters = district !== "all" || year !== "all" || severity !== "all";
  const resetFilters = () => {
    setDistrict("all");
    setYear("all");
    setSeverity("all");
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        <div className="mb-6">
          <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-brand-700">
            <History className="h-4 w-4" /> Flood history
          </p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-navy-950">
            Past flood events in Pakistan
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Every verified flood event on record, with rainfall, affected
            population, and sources. Filter by district, year, or severity to
            see what happened where.
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="flex flex-wrap items-center gap-3 pt-6">
            <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
              District
              <select
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className={selectClass}
              >
                <option value="all">All districts</option>
                {districts.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
              Year
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className={selectClass}
              >
                <option value="all">All years</option>
                {years.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
              Severity
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className={selectClass}
              >
                <option value="all">All severities</option>
                {severities.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            {hasFilters && (
              <button
                type="button"
                onClick={resetFilters}
                className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Reset
              </button>
            )}
            <span className="ml-auto text-xs text-slate-500">
              {loading ? "Loading…" : `${filtered.length} events shown`}
            </span>
          </CardContent>
        </Card>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-52 w-full rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="font-semibold text-navy-950">
                Could not load flood history
              </p>
              <p className="mt-1 text-sm text-slate-500">{error}</p>
              <button
                type="button"
                onClick={refetch}
                className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Try again
              </button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Stats */}
            <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
              {[
                { label: "Events", value: String(stats.events) },
                {
                  label: "People affected",
                  value: formatNumber(stats.affected),
                },
                { label: "Districts hit", value: String(stats.districts) },
                {
                  label: "Worst year",
                  value: stats.worstYear ? String(stats.worstYear) : "—",
                },
              ].map((s) => (
                <Card key={s.label}>
                  <CardContent className="pt-5">
                    <p className="text-2xl font-extrabold text-navy-950">
                      {s.value}
                    </p>
                    <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                      {s.label}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Event cards */}
            {filtered.length === 0 ? (
              <EmptyState
                title="No events match these filters"
                description="Try a different district, year, or severity."
                actionLabel="Reset filters"
                onAction={resetFilters}
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((e) => (
                  <Card
                    key={e.event_id}
                    className="transition-shadow hover:shadow-md"
                  >
                    <CardContent className="pt-5">
                      <div className="flex items-start justify-between gap-2">
                        <Badge
                          variant="outline"
                          className={severityStyle(e.severity_label)}
                        >
                          {e.severity_label}
                        </Badge>
                        <span className="flex items-center gap-1 text-xs text-slate-500">
                          <CalendarDays className="h-3.5 w-3.5" />
                          {formatDate(e.event_date)}
                        </span>
                      </div>
                      <h3 className="mt-3 flex items-center gap-1.5 font-bold text-navy-950">
                        <MapPin className="h-4 w-4 shrink-0 text-brand-600" />
                        {e.district_name}
                        {e.province && (
                          <span className="font-normal text-slate-500">
                            · {e.province}
                          </span>
                        )}
                      </h3>
                      {e.damage_description && (
                        <p className="mt-2 text-sm leading-relaxed text-slate-600">
                          {e.damage_description}
                        </p>
                      )}
                      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-sm">
                        <div>
                          <dt className="flex items-center gap-1 text-xs font-medium text-slate-500">
                            <Droplets className="h-3.5 w-3.5" /> Rainfall
                          </dt>
                          <dd className="mt-0.5 font-semibold text-navy-950">
                            {e.rainfall_mm !== null
                              ? `${e.rainfall_mm} mm`
                              : "Not recorded"}
                          </dd>
                        </div>
                        <div>
                          <dt className="flex items-center gap-1 text-xs font-medium text-slate-500">
                            <Users className="h-3.5 w-3.5" /> Affected
                          </dt>
                          <dd className="mt-0.5 font-semibold text-navy-950">
                            {formatNumber(e.affected_population)}
                          </dd>
                        </div>
                      </dl>
                      {e.source && (
                        <p className="mt-3 text-xs text-slate-400">
                          Source: {e.source}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
