"use client";

import { useMemo, useState, type FormEvent } from "react";
import {
  Megaphone,
  PhoneCall,
  Tent,
  Loader2,
  TriangleAlert,
  CheckCircle2,
  ClipboardList,
} from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { StatCard } from "@/components/StatCard";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useApi } from "@/lib/api/hooks";
import { gisApi, reportsApi } from "@/lib/api/endpoints";
import type { ReportCategory } from "@/lib/api/types";

const categories: { value: ReportCategory; label: string }[] = [
  { value: "flood_water", label: "Flood water sighting" },
  { value: "road_blockage", label: "Road blockage" },
  { value: "rescue_request", label: "Rescue request" },
  { value: "medical_emergency", label: "Medical emergency" },
];

const statusVariant: Record<string, "info" | "medium" | "high" | "low" | "outline"> = {
  pending: "medium",
  verified: "info",
  rejected: "outline",
  resolved: "low",
};

function ReportForm({ onSubmitted }: { onSubmitted: () => void }) {
  const districts = useApi(() => gisApi.districts());
  const [district, setDistrict] = useState("");
  const [category, setCategory] = useState<ReportCategory>("flood_water");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const names = useMemo(
    () =>
      (districts.data?.features ?? [])
        .map((f) => String(f.properties?.district_name ?? ""))
        .filter(Boolean)
        .sort(),
    [districts.data],
  );

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      await reportsApi.submit({
        district_name: district,
        category,
        description: description.trim(),
      });
      setDone(true);
      setDescription("");
      onSubmitted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit the report.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Report a field event</CardTitle>
        <CardDescription>
          Reports go to a triage queue; authorities verify each one before action
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <TriangleAlert />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {done && (
            <Alert variant="info">
              <CheckCircle2 />
              <AlertDescription>
                Report submitted. It is now pending verification by the
                authorities.
              </AlertDescription>
            </Alert>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="district">District</Label>
              <select
                id="district"
                required
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-600"
              >
                <option value="">Select district…</option>
                {names.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value as ReportCategory)}
                className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-600"
              >
                {categories.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">What do you observe?</Label>
            <textarea
              id="description"
              required
              minLength={5}
              rows={4}
              placeholder="Describe water levels, blocked roads, people needing help…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="flex w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-600"
            />
          </div>
          <Button type="submit" variant="brand" disabled={busy}>
            {busy && <Loader2 className="animate-spin" />}
            <Megaphone /> {busy ? "Submitting…" : "Submit report"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function VolunteerPortalPage() {
  const myReports = useApi(() => reportsApi.mine());
  const contacts = useApi(() => gisApi.emergencyContacts());
  const shelters = useApi(() => gisApi.shelters());

  const shelterList = useMemo(
    () =>
      (shelters.data?.features ?? []).map((f) => ({
        name: String(f.properties?.name ?? "Shelter"),
        district: String(f.properties?.district_name ?? "—"),
        capacity:
          typeof f.properties?.capacity === "number"
            ? f.properties.capacity
            : null,
      })),
    [shelters.data],
  );

  return (
    <DashboardShell
      title="Volunteer Portal"
      subtitle="Field reporting and community coordination for NGOs and volunteers"
      allowedRoles={["ngo", "volunteer"]}
    >
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="My reports"
          value={myReports.data?.length ?? "—"}
          hint="field reports submitted"
          icon={ClipboardList}
          accent="navy"
          loading={myReports.loading}
        />
        <StatCard
          label="Shelters listed"
          value={shelterList.length || "—"}
          hint="across monitored districts"
          icon={Tent}
          accent="emerald"
          loading={shelters.loading}
        />
        <StatCard
          label="Emergency contacts"
          value={contacts.data?.length ?? "—"}
          hint="rescue & helpline numbers"
          icon={PhoneCall}
          accent="red"
          loading={contacts.loading}
        />
      </div>

      <div className="mt-8 grid gap-5 xl:grid-cols-2">
        {/* Report form */}
        <section id="report" className="scroll-mt-28">
          <h2 className="mb-3 text-lg font-semibold text-navy-950">
            Submit a field report
          </h2>
          <ReportForm onSubmitted={myReports.refetch} />

          <h2 className="mb-3 mt-8 text-lg font-semibold text-navy-950">
            My reports
          </h2>
          {myReports.loading && <Skeleton className="h-32" />}
          {myReports.error && (
            <p className="text-sm text-red-600">
              Could not load your reports: {myReports.error}
            </p>
          )}
          {myReports.data && myReports.data.length === 0 && (
            <EmptyState
              title="No reports yet"
              description="Your submitted field reports will appear here with their verification status."
            />
          )}
          {myReports.data && myReports.data.length > 0 && (
            <div className="space-y-2">
              {myReports.data.map((r) => (
                <Card key={r.id}>
                  <CardContent className="flex items-start justify-between gap-3 p-4">
                    <div>
                      <p className="text-sm font-semibold text-navy-950">
                        {r.category.replace(/_/g, " ")} · {r.district_name ?? "—"}
                      </p>
                      <p className="mt-1 text-sm text-slate-600">{r.description}</p>
                      <p className="mt-1 text-xs text-slate-400">
                        {new Date(r.created_at).toLocaleString("en-PK", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                      </p>
                    </div>
                    <Badge variant={statusVariant[r.status] ?? "outline"}>
                      {r.status}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Shelters + contacts */}
        <div>
          <section id="shelters" className="scroll-mt-28">
            <h2 className="mb-3 text-lg font-semibold text-navy-950">
              Shelters
            </h2>
            {shelters.loading && <Skeleton className="h-40" />}
            {shelters.error && (
              <p className="text-sm text-red-600">
                Shelters unavailable: {shelters.error}
              </p>
            )}
            {shelters.data && shelterList.length === 0 && (
              <EmptyState
                title="No shelters listed"
                description="Shelter locations will appear here once registered."
              />
            )}
            {shelterList.length > 0 && (
              <Card>
                <CardContent className="divide-y divide-slate-100 p-0">
                  {shelterList.slice(0, 8).map((s, i) => (
                    <div key={`${s.name}-${i}`} className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-emerald-700">
                          <Tent className="h-4 w-4" />
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-navy-950">{s.name}</p>
                          <p className="text-xs text-slate-500">{s.district}</p>
                        </div>
                      </div>
                      {s.capacity !== null && (
                        <Badge variant="outline">Capacity {s.capacity}</Badge>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </section>

          <section id="community" className="mt-8 scroll-mt-28">
            <h2 className="mb-3 text-lg font-semibold text-navy-950">
              Emergency contacts
            </h2>
            {contacts.loading && <Skeleton className="h-40" />}
            {contacts.error && (
              <p className="text-sm text-red-600">
                Contacts unavailable: {contacts.error}
              </p>
            )}
            {contacts.data && contacts.data.length === 0 && (
              <EmptyState
                title="No contacts listed"
                description="Emergency contacts will appear here once registered."
              />
            )}
            {contacts.data && contacts.data.length > 0 && (
              <Card>
                <CardContent className="divide-y divide-slate-100 p-0">
                  {contacts.data.slice(0, 8).map((c, i) => (
                    <div key={`${c.phone}-${i}`} className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-red-50 text-red-700">
                          <PhoneCall className="h-4 w-4" />
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-navy-950">{c.name}</p>
                          <p className="text-xs text-slate-500">
                            {[c.organization, c.district_name].filter(Boolean).join(" · ")}
                          </p>
                        </div>
                      </div>
                      <a
                        href={`tel:${c.phone}`}
                        className="text-sm font-bold text-brand-600 hover:underline"
                      >
                        {c.phone}
                      </a>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
            <Card className="mt-4 border-red-200 bg-red-50">
              <CardContent className="p-4 text-sm text-red-900">
                <strong>Rescue requests are urgent.</strong> If lives are at
                immediate risk, call Rescue 1122 directly instead of waiting
                for report verification.
              </CardContent>
            </Card>
          </section>
        </div>
      </div>
    </DashboardShell>
  );
}
