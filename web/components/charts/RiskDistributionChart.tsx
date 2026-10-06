"use client";

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/api/hooks";
import { dashboardApi } from "@/lib/api/endpoints";

function DistributionTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { name: string; value: number; payload: { color: string } }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const s = payload[0];
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <p className="flex items-center gap-2 font-bold text-navy-950">
        <span
          className="inline-block h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: s.payload.color }}
        />
        {s.name} risk
      </p>
      <p className="mt-0.5 text-slate-600">
        {s.value} district{s.value === 1 ? "" : "s"}
      </p>
    </div>
  );
}

/** Risk distribution donut from GET /dashboard/risk-distribution. */
export function RiskDistributionChart() {
  const { data, loading, error } = useApi(() => dashboardApi.riskDistribution());

  const slices = data
    ? [
        { name: "Low", value: data.low, color: "#10b981" },
        { name: "Medium", value: data.medium, color: "#f59e0b" },
        { name: "High", value: data.high, color: "#dc2626" },
      ]
    : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Risk Distribution</CardTitle>
        <CardDescription>Monitored districts by current risk level</CardDescription>
      </CardHeader>
      <CardContent>
        {loading && <Skeleton className="h-64 w-full" />}
        {error && <p className="py-10 text-center text-sm text-red-600">{error}</p>}
        {data && (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={slices}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                >
                  {slices.map((s) => (
                    <Cell key={s.name} fill={s.color} />
                  ))}
                </Pie>
                <Tooltip content={<DistributionTooltip />} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
