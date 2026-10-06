"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Droplets, Radio, ArrowRight, MapPin, BellRing } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { publicApi, type SituationResponse } from "@/lib/api/public";
import { formatProbability, probabilityPct } from "@/lib/format";
import { cn } from "@/lib/utils";

const severityStyle: Record<string, string> = {
  emergency: "border-l-4 border-l-red-600",
  warning: "border-l-4 border-l-orange-500",
  watch: "border-l-4 border-l-amber-400",
  info: "border-l-4 border-l-sky-500",
};

function Skeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-36 animate-pulse rounded-xl bg-slate-200" />
      ))}
    </div>
  );
}

/**
 * Live flood situation strip for the public homepage. Pulls the
 * unauthenticated /public/situation endpoint: current high-risk districts,
 * active alerts, and the latest risk updates.
 */
export function LiveSituationSection() {
  const [data, setData] = useState<SituationResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    publicApi
      .situation()
      .then((s) => {
        if (!cancelled) setData(s);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const updatedAt = data?.generated_at
    ? new Date(data.generated_at).toLocaleString("en-PK", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : null;

  return (
    <section id="live-situation" className="border-y border-slate-200 bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-red-600">
              <Radio className="h-4 w-4" /> Live situation
            </p>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-navy-950">
              Flood situation right now
            </h2>
            <p className="mt-2 max-w-2xl text-slate-600">
              Current high-risk districts, active alerts, and the latest risk
              assessments — updated by the early-warning cycle.
              {updatedAt && (
                <span className="mt-1 block text-xs text-slate-400">
                  Last updated {updatedAt}
                </span>
              )}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/risk-check">
              <Button variant="brand" size="sm">
                Check my district <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/map">
              <Button variant="outline" size="sm">
                <MapPin className="h-4 w-4" /> Open risk map
              </Button>
            </Link>
          </div>
        </div>

        <div className="mt-8">
          {error && (
            <Card>
              <CardContent className="p-6 text-sm text-slate-600">
                Live data is temporarily unavailable. The information below is
                refreshed automatically — please try again shortly, and in an
                emergency call <strong>Rescue 1122</strong> or{" "}
                <strong>PDMA Sindh 1736</strong>.
              </CardContent>
            </Card>
          )}
          {!error && !data && <Skeleton />}
          {data && (
            <div className="space-y-8">
              {/* High-risk districts */}
              <div>
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-500">
                  <Droplets className="h-4 w-4 text-red-600" /> High-risk districts
                </h3>
                {data.high_risk_districts.length === 0 ? (
                  <p className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                    No district is currently assessed at high risk. Conditions
                    are monitored continuously.
                  </p>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {data.high_risk_districts.slice(0, 6).map((d) => (
                      <Card key={d.district_name} className="border-l-4 border-l-red-600">
                        <CardContent className="p-5">
                          <div className="flex items-center justify-between gap-2">
                            <p className="font-bold text-navy-950">{d.district_name}</p>
                            <Badge variant="high">
                              HIGH · {formatProbability(d.probability)}
                            </Badge>
                          </div>
                          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-red-600"
                              style={{ width: `${probabilityPct(d.probability) ?? 0}%` }}
                            />
                          </div>
                          {d.top_factors.length > 0 && (
                            <p className="mt-3 text-xs text-slate-500">
                              Key factors:{" "}
                              {d.top_factors
                                .slice(0, 3)
                                .map((f) => f.feature.replace(/_/g, " "))
                                .join(", ")}
                            </p>
                          )}
                          <Link
                            href={`/risk-check?district=${encodeURIComponent(d.district_name)}`}
                            className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-600"
                          >
                            Full assessment <ArrowRight className="h-3 w-3" />
                          </Link>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Active alerts */}
              <div>
                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-500">
                  <BellRing className="h-4 w-4 text-orange-600" /> Active alerts
                </h3>
                {data.active_alerts.length === 0 ? (
                  <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    No active alerts at the moment.
                  </p>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    {data.active_alerts.slice(0, 4).map((a) => (
                      <Card key={a.id} className={cn(severityStyle[a.severity] ?? "")}>
                        <CardContent className="flex items-start gap-3 p-5">
                          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-orange-600" />
                          <div>
                            <p className="font-semibold text-navy-950">{a.title}</p>
                            <p className="mt-1 text-sm text-slate-600">{a.message}</p>
                            <p className="mt-2 text-xs text-slate-400">
                              {a.district_name}
                              {a.issued_at &&
                                ` · ${new Date(a.issued_at).toLocaleString("en-PK", {
                                  dateStyle: "medium",
                                  timeStyle: "short",
                                })}`}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Latest risk updates */}
              {data.latest_predictions.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                    Latest risk updates
                  </h3>
                  <div className="overflow-hidden rounded-xl border border-slate-200">
                    <ul className="divide-y divide-slate-100">
                      {data.latest_predictions.slice(0, 5).map((p) => (
                        <li
                          key={p.district_name}
                          className="flex items-center justify-between gap-3 bg-white px-4 py-3"
                        >
                          <span className="text-sm font-medium text-navy-950">
                            {p.district_name}
                            <span className="ml-2 text-xs font-normal text-slate-400">
                              {p.predicted_at
                                ? new Date(p.predicted_at).toLocaleString("en-PK", {
                                    dateStyle: "medium",
                                    timeStyle: "short",
                                  })
                                : ""}
                            </span>
                          </span>
                          <Badge
                            variant={
                              p.risk_level === "HIGH"
                                ? "high"
                                : p.risk_level === "MEDIUM"
                                  ? "medium"
                                  : "low"
                            }
                          >
                            {p.risk_level} · {formatProbability(p.probability)}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
