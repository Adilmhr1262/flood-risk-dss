"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/api/hooks";
import { dashboardApi } from "@/lib/api/endpoints";

function RainfallTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number | string }[];
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const mm = Number(payload[0].value);
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <p className="font-bold text-navy-950">{label}</p>
      <p className="mt-0.5 text-slate-600">
        Rainfall: <span className="font-semibold text-navy-800">{mm.toFixed(1)} mm</span>
      </p>
      <p className="text-slate-500">
        {mm >= 200 ? "Very heavy monsoon rain" : mm >= 100 ? "Heavy rain" : mm >= 50 ? "Moderate rain" : "Light rain"}
      </p>
    </div>
  );
}

/** Monthly rainfall trend chart from GET /dashboard/rainfall-trends. */
export function RainfallChart() {
  const { data, loading, error } = useApi(() => dashboardApi.rainfallTrends());

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Rainfall Trends</CardTitle>
        <CardDescription>Observed monsoon rainfall across monitored districts (mm)</CardDescription>
      </CardHeader>
      <CardContent>
        {loading && <Skeleton className="h-64 w-full" />}
        {error && <p className="py-10 text-center text-sm text-red-600">{error}</p>}
        {data && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} stroke="#64748b" interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 11 }} stroke="#64748b" />
                <Tooltip content={<RainfallTooltip />} />
                <Area type="monotone" dataKey="rainfall_mm" stroke="#1f4c8a" fill="#dbe6f5" strokeWidth={2} />
                <Line type="monotone" dataKey="rainfall_mm" stroke="#1f4c8a" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
