import { Droplets } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { RiskAssessmentOutput } from "@/lib/api/types";
import { formatProbability, probabilityPct } from "@/lib/format";
import { cn } from "@/lib/utils";

const levelStyle: Record<string, string> = {
  LOW: "border-l-4 border-l-emerald-500",
  MEDIUM: "border-l-4 border-l-amber-500",
  HIGH: "border-l-4 border-l-red-600",
};

const badgeVariant = (level: string) =>
  level === "HIGH" ? "high" : level === "MEDIUM" ? "medium" : "low";

/**
 * District flood-risk assessment card, rendered from a real
 * POST /risk/predict response. Shows probability, level, key factors,
 * contributing features, and recommended actions.
 */
export function RiskCard({ result }: { result: RiskAssessmentOutput }) {
  const pct = formatProbability(result.probability);

  return (
    <Card className={cn("overflow-hidden", levelStyle[result.risk_level])}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Droplets className="h-4 w-4 text-navy-700" />
            {result.district_name}
          </CardTitle>
          <Badge variant={badgeVariant(result.risk_level) as "low" | "medium" | "high"}>
            {result.risk_level} · {pct}
          </Badge>
        </div>
        <p className="text-xs text-slate-500">
          Model {result.model_version}
          {result.model_requested ? ` · requested ${result.model_requested}` : ""}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                result.risk_level === "HIGH"
                  ? "bg-red-600"
                  : result.risk_level === "MEDIUM"
                    ? "bg-amber-500"
                    : "bg-emerald-500",
              )}
              style={{ width: `${probabilityPct(result.probability) ?? 0}%` }}
            />
          </div>
        </div>

        {result.main_factors.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Key risk factors
            </p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-navy-900">
              {result.main_factors.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        )}

        {result.feature_contributions.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Top contributing signals
            </p>
            <div className="flex flex-wrap gap-1.5">
              {result.feature_contributions.slice(0, 5).map((fc) => (
                <Badge key={fc.feature} variant="outline">
                  {fc.feature}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {result.recommendations.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Recommended actions
            </p>
            <ul className="space-y-1.5 text-sm text-navy-900">
              {result.recommendations.map((r) => (
                <li key={r} className="flex gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.note && (
          <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
            {result.note}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
