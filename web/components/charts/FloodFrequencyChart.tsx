"use client";

import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/api/hooks";
import { gisApi } from "@/lib/api/endpoints";

interface YearBucket {
  year: number;
  events: number;
  /** severity label -> count, for the hover tooltip */
  bySeverity: Record<string, number>;
  affected: number;
}

const BAR_COLOR = "#ea580c";

function FloodTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: YearBucket }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const b = payload[0].payload;
  const sevEntries = Object.entries(b.bySeverity).sort((a, b) => b[1] - a[1]);
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <p className="font-bold text-navy-950">
        {b.year} — {b.events} event{b.events === 1 ? "" : "s"}
      </p>
      {sevEntries.length > 0 && (
        <ul className="mt-1 space-y-0.5 text-slate-600">
          {sevEntries.map(([sev, n]) => (
            <li key={sev} className="flex justify-between gap-4">
              <span>{sev}</span>
              <span className="font-semibold">{n}</span>
            </li>
          ))}
        </ul>
      )}
      {b.affected > 0 && (
        <p className="mt-1 text-slate-500">
          Affected: {b.affected.toLocaleString()} people
        </p>
      )}
    </div>
  );
}

/**
 * Interactive flood-frequency chart, aggregated client-side from the live
 * GET /gis/historical-floods GeoJSON (52 verified events, 2010–2024).
 *
 * Controls: district filter, year-range selection. Hover any bar for a
 * severity breakdown and affected-population total for that year.
 */
export function FloodFrequencyChart() {
  const { data, loading, error } = useApi(() => gisApi.historicalFloods());
  const [district, setDistrict] = useState("all");
  const [fromYear, setFromYear] = useState<number | "">(2010);
  const [toYear, setToYear] = useState<number | "">(2026);

  const districts = useMemo(() => {
    const names = new Set<string>();
    for (const f of data?.features ?? []) {
      const n = f.properties?.district_name;
      if (typeof n === "string" && n) names.add(n);
    }
    return [...names].sort();
  }, [data]);

  const buckets: YearBucket[] = useMemo(() => {
    const map = new Map<number, YearBucket>();
    const from = fromYear === "" ? 2010 : fromYear;
    const to = toYear === "" ? 2026 : toYear;
    for (const f of data?.features ?? []) {
      const p = f.properties ?? {};
      const year = Number(p.year);
      const dname = String(p.district_name ?? "");
      if (!Number.isFinite(year) || year < from || year > to) continue;
      if (district !== "all" && dname !== district) continue;
      let b = map.get(year);
      if (!b) {
        b = { year, events: 0, bySeverity: {}, affected: 0 };
        map.set(year, b);
      }
      b.events += 1;
      const sev = String(p.severity_label ?? "Unknown");
      b.bySeverity[sev] = (b.bySeverity[sev] ?? 0) + 1;
      const aff = Number(p.affected_population);
      if (Number.isFinite(aff)) b.affected += aff;
    }
    return [...map.values()].sort((a, b) => a.year - b.year);
  }, [data, district, fromYear, toYear]);

  const total = buckets.reduce((s, b) => s + b.events, 0);
  const maxYear = buckets.length > 0 ? Math.max(...buckets.map((b) => b.events)) : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">Flood Frequency</CardTitle>
            <CardDescription>
              Verified flood events per year{district !== "all" ? ` — ${district}` : " across Sindh"}
              {" · "}{total} events in range
            </CardDescription>
          </div>
        </div>
        {/* Controls */}
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
            District
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="h-9 rounded-lg border border-slate-300 bg-white px-2 text-xs text-navy-950 focus:border-brand-500 focus:outline-none"
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
            From
            <input
              type="number"
              min={2010}
              max={2026}
              value={fromYear}
              onChange={(e) =>
                setFromYear(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="h-9 w-20 rounded-lg border border-slate-300 bg-white px-2 text-xs text-navy-950 focus:border-brand-500 focus:outline-none"
            />
          </label>
          <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
            To
            <input
              type="number"
              min={2010}
              max={2026}
              value={toYear}
              onChange={(e) =>
                setToYear(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="h-9 w-20 rounded-lg border border-slate-300 bg-white px-2 text-xs text-navy-950 focus:border-brand-500 focus:outline-none"
            />
          </label>
        </div>
      </CardHeader>
      <CardContent>
        {loading && <Skeleton className="h-64 w-full" />}
        {error && <p className="py-10 text-center text-sm text-red-600">{error}</p>}
        {!loading && !error && buckets.length === 0 && (
          <p className="py-10 text-center text-sm text-slate-500">
            No events match this filter combination.
          </p>
        )}
        {buckets.length > 0 && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={buckets} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#64748b" interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 11 }} stroke="#64748b" allowDecimals={false} />
                <Tooltip content={<FloodTooltip />} cursor={{ fill: "#fff7ed" }} />
                <Bar dataKey="events" radius={[4, 4, 0, 0]}>
                  {buckets.map((b) => (
                    <Cell
                      key={b.year}
                      fill={b.events === maxYear && maxYear > 0 ? "#dc2626" : BAR_COLOR}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
