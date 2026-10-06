"use client";

import { useEffect, useState } from "react";
import { Activity, CheckCircle2, Database, Loader2, Server, XCircle, BellRing } from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { publicApi } from "@/lib/api/public";

interface StatusPayload {
  status: string;
  env: string;
  database: { ok: boolean; error: string | null };
  model: { name: string; loaded: boolean; available: string[] };
  scheduler: { enabled: boolean; cycle_minutes: number };
}

function Row({ icon: Icon, label, ok, detail }: { icon: typeof Server; label: string; ok: boolean | null; detail: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 py-3 last:border-0">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-navy-700" />
        <div>
          <p className="text-sm font-semibold text-navy-950">{label}</p>
          <p className="text-xs text-slate-500">{detail}</p>
        </div>
      </div>
      {ok === null ? (
        <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
      ) : ok ? (
        <Badge variant="low" className="flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5" /> Operational
        </Badge>
      ) : (
        <Badge variant="emergency" className="flex items-center gap-1">
          <XCircle className="h-3.5 w-3.5" /> Down
        </Badge>
      )}
    </div>
  );
}

/**
 * Public service status page: API reachability, database, prediction
 * model, and early-warning scheduler — no login required.
 */
export default function StatusPage() {
  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    publicApi
      .serviceStatus()
      .then((s) => {
        if (cancelled) return;
        setApiUp(true);
        setStatus(s);
      })
      .catch(() => {
        if (!cancelled) {
          setApiUp(false);
          setFailed(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6">
        <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-brand-700">
          <Activity className="h-4 w-4" /> System status
        </p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-navy-950">
          Service status
        </h1>
        <p className="mt-2 text-slate-600">
          Live health of the FloodSafe Pakistan platform components. Refreshes
          on each visit.
        </p>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">
              {failed ? "Platform unreachable" : apiUp ? "All systems reporting" : "Checking…"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {failed ? (
              <p className="text-sm text-red-600">
                The backend API did not respond. The public pages may be showing
                cached content; try again shortly.
              </p>
            ) : (
              <>
                <Row
                  icon={Server}
                  label="API server"
                  ok={apiUp}
                  detail={status ? `Environment: ${status.env}` : "Responding to health checks"}
                />
                <Row
                  icon={Database}
                  label="Database"
                  ok={status ? status.database.ok : null}
                  detail={
                    status
                      ? status.database.ok
                        ? "PostgreSQL + PostGIS connected"
                        : `Connection failed${status.database.error ? `: ${status.database.error}` : ""}`
                      : "Waiting for API…"
                  }
                />
                <Row
                  icon={Activity}
                  label="Prediction model"
                  ok={status ? status.model.loaded : null}
                  detail={
                    status
                      ? status.model.loaded
                        ? `Active model: ${status.model.name}`
                        : `Model ${status.model.name} not loaded`
                      : "Waiting for API…"
                  }
                />
                <Row
                  icon={BellRing}
                  label="Early-warning scheduler"
                  ok={status ? true : null}
                  detail={
                    status
                      ? status.scheduler.enabled
                        ? `Running every ${status.scheduler.cycle_minutes} minutes`
                        : "Disabled on this deployment"
                      : "Waiting for API…"
                  }
                />
              </>
            )}
          </CardContent>
        </Card>

        <p className="mt-4 text-xs text-slate-500">
          Status is served by the backend <code>/api/v1/status</code> endpoint.
          During a real flood emergency, always confirm warnings through
          Rescue 1122 or your district PDMA control room.
        </p>
      </main>
      <Footer />
    </div>
  );
}
