"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Search,
  Droplets,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  Info,
  MapPin,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { publicApi, RISK_COLORS, type PublicDistrict, type RiskCheckResponse } from "@/lib/api/public";
import { probabilityPct } from "@/lib/format";
import { MyLocationCard } from "@/components/MyLocationCard";
import { cn } from "@/lib/utils";

function levelBadge(level: string): "high" | "medium" | "low" {
  return level === "HIGH" ? "high" : level === "MEDIUM" ? "medium" : "low";
}

function Gauge({ probability, level }: { probability: number; level: string }) {
  const pct = probabilityPct(probability) ?? 0;
  const color = RISK_COLORS[level as keyof typeof RISK_COLORS] ?? "#64748b";
  const r = 64;
  const circumference = Math.PI * r;
  const filled = (pct / 100) * circumference;
  return (
    <div className="relative mx-auto h-36 w-40">
      <svg viewBox="0 0 160 96" className="h-full w-full">
        <path
          d={`M 16 88 A ${r} ${r} 0 0 1 144 88`}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d={`M 16 88 A ${r} ${r} 0 0 1 144 88`}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <p className="text-4xl font-extrabold text-navy-950">{pct}%</p>
        <Badge variant={levelBadge(level)} className="mt-1">
          {level} RISK
        </Badge>
      </div>
    </div>
  );
}

/**
 * Public flood-risk checker — no login required. A citizen picks their
 * district and gets the current risk probability, category, contributing
 * factors, and safety recommendations from GET /public/risk-check.
 */
function RiskCheckerInner() {
  const searchParams = useSearchParams();
  const [districts, setDistricts] = useState<PublicDistrict[]>([]);
  const [selected, setSelected] = useState("");
  const [result, setResult] = useState<RiskCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const check = useCallback(async (district: string) => {
    if (!district) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await publicApi.riskCheck(district);
      setResult(r);
    } catch {
      setError(
        "Could not assess this district right now. Please try again shortly.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    publicApi
      .districts()
      .then((d) => {
        if (cancelled) return;
        setDistricts(d.districts);
        const preselect = searchParams.get("district");
        if (preselect) {
          const match = d.districts.find(
            (x) => x.district_name.toLowerCase() === preselect.toLowerCase(),
          );
          if (match) {
            setSelected(match.district_name);
            void check(match.district_name);
          }
        }
      })
      .catch(() => {
        if (!cancelled)
          setError("Could not load the district list. Please try again.");
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Auto-run when a district is preselected via ?district= is handled in the
  // districts-load effect above via checkRef.

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-10 sm:px-6">
        <div className="text-center">
          <p className="flex items-center justify-center gap-2 text-sm font-semibold uppercase tracking-wider text-brand-700">
            <Droplets className="h-4 w-4" /> No login needed
          </p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-navy-950 sm:text-4xl">
            Check flood risk for your district
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-slate-600">
            Select your district to see the current flood risk assessment —
            probability, what is driving it, and what you should do. Powered by
            the same prediction engine used by the early-warning system.
          </p>
        </div>

        <div className="mx-auto mt-8 max-w-2xl">
          <MyLocationCard />
        </div>

        <Card className="mx-auto mt-8 max-w-2xl">
          <CardContent className="p-6">
            <label
              htmlFor="district"
              className="mb-2 block text-sm font-semibold text-navy-950"
            >
              Your district
            </label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <select
                id="district"
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
                className="h-11 flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm text-navy-950 focus:border-brand-500 focus:outline-none"
              >
                <option value="">Select a district…</option>
                {districts.map((d) => (
                  <option key={d.district_name} value={d.district_name}>
                    {d.district_name}
                    {d.province ? ` — ${d.province}` : ""}
                  </option>
                ))}
              </select>
              <Button
                variant="brand"
                size="lg"
                className="h-11"
                disabled={!selected || loading}
                onClick={() => check(selected)}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Check risk
              </Button>
            </div>
            {error && (
              <p className="mt-3 flex items-start gap-2 text-sm text-red-700">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
              </p>
            )}
          </CardContent>
        </Card>

        {result && (
          <div className="mt-8 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-brand-700" />
                  {result.district_name}
                  {result.province && (
                    <span className="text-sm font-normal text-slate-500">
                      {result.province}
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-8 md:grid-cols-[auto_1fr]">
                <Gauge probability={result.probability} level={result.risk_level} />
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                    What this means
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-700">
                    {result.risk_level === "HIGH" &&
                      "Conditions indicate a high likelihood of flooding. Take protective action now: move valuables and livestock to higher ground, prepare to evacuate if authorities advise, and monitor official alerts."}
                    {result.risk_level === "MEDIUM" &&
                      "Conditions show an elevated flood risk. Stay alert: keep emergency supplies ready, avoid low-lying riverbank areas during heavy rain, and follow official advisories."}
                    {result.risk_level === "LOW" &&
                      "Current conditions show a low flood risk. No immediate action is needed, but stay informed during the monsoon season."}
                  </p>
                  <p className="mt-3 text-xs text-slate-400">
                    Assessed {new Date(result.checked_at).toLocaleString("en-PK")} ·
                    Model {result.model_version}
                    {result.note ? ` · ${result.note}` : ""}
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Info className="h-4 w-4 text-brand-700" />
                    Contributing factors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.main_factors.map((f) => (
                      <li
                        key={f}
                        className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
                      >
                        {f}
                      </li>
                    ))}
                  </ul>
                  {result.feature_contributions.length > 0 && (
                    <div className="mt-4 space-y-2">
                      {result.feature_contributions.slice(0, 6).map((fc) => (
                        <div key={fc.feature} className="text-xs">
                          <div className="flex justify-between text-slate-600">
                            <span className="capitalize">
                              {fc.feature.replace(/_/g, " ")}
                            </span>
                          </div>
                          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                fc.contribution >= 0 ? "bg-orange-500" : "bg-emerald-500",
                              )}
                              style={{
                                width: `${Math.min(100, Math.abs(fc.contribution) * 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    Safety recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.recommendations.map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />
                        {r}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardContent className="p-5">
                <h3 className="text-sm font-semibold text-navy-950">
                  Conditions used for this assessment
                </h3>
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-5">
                  {[
                    ["Rainfall (24h forecast)", `${result.inputs_used.rainfall_mm} mm`],
                    ["Temperature", `${result.inputs_used.temperature_c} °C`],
                    ["Humidity", `${result.inputs_used.humidity_pct} %`],
                    ["Past flood events", `${result.inputs_used.prev_flood_events}`],
                    ["Last severity", `${result.inputs_used.last_severity} / 5`],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-lg bg-slate-50 p-3">
                      <p className="text-[11px] text-slate-500">{label}</p>
                      <p className="mt-1 text-sm font-bold text-navy-950">{value}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex flex-wrap justify-center gap-3 pb-4">
              <Link href="/emergency">
                <Button variant="outline">
                  <AlertTriangle className="h-4 w-4" /> Emergency help
                </Button>
              </Link>
              <Link href="/learn">
                <Button variant="outline">Flood safety guide</Button>
              </Link>
            </div>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}

export default function RiskCheckPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-brand-700" />
        </div>
      }
    >
      <RiskCheckerInner />
    </Suspense>
  );
}
