"use client";

import { useState, type FormEvent } from "react";
import { Loader2, Plus, Trash2, Warehouse, Users, Building2 } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { CommandNav } from "@/components/authority/CommandNav";
import { EmptyState } from "@/components/EmptyState";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useApi } from "@/lib/api/hooks";
import { gisApi, resourcesApi } from "@/lib/api/endpoints";
import type { ResponseTeamCreate, ShelterResource } from "@/lib/api/types";

const SHELTER_STATUSES = ["open", "full", "closed", "maintenance"] as const;
const TEAM_TYPES = ["rescue", "medical", "logistics", "boat"] as const;
const TEAM_STATUSES = ["available", "deployed", "standby"] as const;

function ShelterRow({ shelter, onUpdate }: { shelter: ShelterResource; onUpdate: () => void }) {
  const [occupancy, setOccupancy] = useState(String(shelter.current_occupancy));
  const [status, setStatus] = useState<string>(shelter.status);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dirty = occupancy !== String(shelter.current_occupancy) || status !== shelter.status;

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await resourcesApi.updateShelter(shelter.id, {
        current_occupancy: Number(occupancy),
        status,
      });
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  const pct = shelter.occupancy_pct ?? 0;

  return (
    <tr className="border-b border-slate-100 last:border-0">
      <td className="px-4 py-3">
        <p className="font-medium text-navy-950">{shelter.name}</p>
        <p className="text-xs text-slate-500">{shelter.district_name ?? "—"}</p>
      </td>
      <td className="px-4 py-3 text-slate-600">{shelter.capacity ?? "—"}</td>
      <td className="px-4 py-3">
        {shelter.capacity != null ? (
          <div className="w-36">
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${pct >= 100 ? "bg-red-500" : pct >= 75 ? "bg-amber-500" : "bg-emerald-500"}`}
                style={{ width: `${Math.min(100, pct)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {shelter.current_occupancy}/{shelter.capacity} ({pct.toFixed(0)}%)
            </p>
          </div>
        ) : (
          <span className="text-slate-400">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-slate-600">
        {shelter.availability != null ? shelter.availability : "—"}
      </td>
      <td className="px-4 py-3">
        <div className="flex flex-col gap-1">
          <div className="flex gap-1">
            <Input
              type="number"
              min={0}
              max={shelter.capacity ?? undefined}
              value={occupancy}
              onChange={(e) => setOccupancy(e.target.value)}
              className="h-8 w-20"
              aria-label={`Occupancy for ${shelter.name}`}
            />
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="h-8 rounded-md border border-slate-300 bg-white px-2 text-xs"
              aria-label={`Status for ${shelter.name}`}
            >
              {SHELTER_STATUSES.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <Button size="sm" variant="outline" disabled={!dirty || busy} onClick={save}>
          {busy && <Loader2 className="animate-spin" />} Save
        </Button>
      </td>
    </tr>
  );
}

function TeamForm({ onDone }: { onDone: () => void }) {
  const districts = useApi(() => gisApi.districts());
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [teamType, setTeamType] = useState<ResponseTeamCreate["team_type"]>("rescue");
  const [district, setDistrict] = useState("");
  const [members, setMembers] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const names =
    (districts.data?.features ?? [])
      .map((f) => String(f.properties?.district_name ?? ""))
      .filter(Boolean)
      .sort();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await resourcesApi.createTeam({
        name: name.trim(),
        team_type: teamType,
        district_name: district || null,
        members_count: members ? Number(members) : null,
        contact_phone: phone.trim() || null,
      });
      setOpen(false);
      setName("");
      setDistrict("");
      setMembers("");
      setPhone("");
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the team.");
    } finally {
      setBusy(false);
    }
  }

  if (!open)
    return (
      <Button variant="brand" size="sm" onClick={() => setOpen(true)}>
        <Plus /> Add team
      </Button>
    );

  return (
    <Card>
      <CardContent className="p-4">
        <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2">
          {error && (
            <Alert variant="destructive" className="sm:col-span-2">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="team-name">Team name</Label>
            <Input id="team-name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Dadu Boat Team 1" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="team-type">Type</Label>
            <select id="team-type" value={teamType} onChange={(e) => setTeamType(e.target.value as ResponseTeamCreate["team_type"])} className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              {TEAM_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="team-district">District</Label>
            <select id="team-district" value={district} onChange={(e) => setDistrict(e.target.value)} className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm">
              <option value="">Unassigned</option>
              {names.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="team-members">Members</Label>
            <Input id="team-members" type="number" min={1} value={members} onChange={(e) => setMembers(e.target.value)} placeholder="8" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="team-phone">Contact phone</Label>
            <Input id="team-phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+92-300-…" />
          </div>
          <div className="flex gap-2 sm:col-span-2">
            <Button type="submit" variant="brand" size="sm" disabled={busy}>
              {busy && <Loader2 className="animate-spin" />} Create team
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => setOpen(false)}>Cancel</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export default function ResourcesPage() {
  const shelters = useApi(() => resourcesApi.shelters());
  const teams = useApi(() => resourcesApi.teams());
  const infrastructure = useApi(() => resourcesApi.infrastructure());
  const [teamBusy, setTeamBusy] = useState<string | null>(null);

  async function setTeamStatus(id: string, status: "available" | "deployed" | "standby") {
    setTeamBusy(id);
    try {
      await resourcesApi.updateTeam(id, { status });
      teams.refetch();
    } finally {
      setTeamBusy(null);
    }
  }

  async function deleteTeam(id: string) {
    if (!window.confirm("Delete this team?")) return;
    setTeamBusy(id);
    try {
      await resourcesApi.deleteTeam(id);
      teams.refetch();
    } finally {
      setTeamBusy(null);
    }
  }

  const teamList = teams.data ?? [];
  const deployed = teamList.filter((t) => t.status === "deployed").length;

  return (
    <DashboardShell
      title="Resource Management"
      subtitle="Shelters, response teams and emergency infrastructure"
      allowedRoles={["authority"]}
    >
      <CommandNav />

      {/* Shelters */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-navy-950">
          <Warehouse className="h-5 w-5" /> Shelter monitoring
        </h2>
        {shelters.loading && <Skeleton className="h-48" />}
        {shelters.error && <p className="text-sm text-red-600">Shelters unavailable: {shelters.error}</p>}
        {shelters.data && shelters.data.length === 0 && (
          <EmptyState title="No shelters registered" description="Shelter records will appear here once added." />
        )}
        {shelters.data && shelters.data.length > 0 && (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-navy-950 text-left text-white">
                      <th className="px-4 py-3 font-semibold">Shelter</th>
                      <th className="px-4 py-3 font-semibold">Capacity</th>
                      <th className="px-4 py-3 font-semibold">Occupancy</th>
                      <th className="px-4 py-3 font-semibold">Available</th>
                      <th className="px-4 py-3 font-semibold">Update</th>
                      <th className="px-4 py-3 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shelters.data.map((sh) => (
                      <ShelterRow key={sh.id} shelter={sh} onUpdate={shelters.refetch} />
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Teams */}
      <section className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-navy-950">
            <Users className="h-5 w-5" /> Response teams
            {teamList.length > 0 && (
              <span className="text-sm font-normal text-slate-500">
                {deployed} of {teamList.length} deployed
              </span>
            )}
          </h2>
          <TeamForm onDone={teams.refetch} />
        </div>
        {teams.loading && <Skeleton className="h-40" />}
        {teams.error && <p className="text-sm text-red-600">Teams unavailable: {teams.error}</p>}
        {teams.data && teamList.length === 0 && (
          <EmptyState title="No teams registered" description="Add the first response team with the button above." />
        )}
        {teamList.length > 0 && (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {teamList.map((t) => (
              <Card key={t.id}>
                <CardContent className="space-y-3 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-navy-950">{t.name}</p>
                      <p className="text-xs text-slate-500">
                        {t.team_type} · {t.district_name ?? "Unassigned"}
                        {t.members_count ? ` · ${t.members_count} members` : ""}
                      </p>
                    </div>
                    <Badge variant={t.status === "deployed" ? "emergency" : t.status === "standby" ? "watch" : "low"}>
                      {t.status}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {TEAM_STATUSES.filter((st) => st !== t.status).map((st) => (
                      <Button
                        key={st}
                        size="sm"
                        variant="outline"
                        disabled={teamBusy === t.id}
                        onClick={() => setTeamStatus(t.id, st)}
                      >
                        {teamBusy === t.id && <Loader2 className="animate-spin" />}
                        {st === "deployed" ? "Deploy" : st === "available" ? "Stand down" : "Standby"}
                      </Button>
                    ))}
                    <Button size="sm" variant="ghost" disabled={teamBusy === t.id} onClick={() => deleteTeam(t.id)} aria-label={`Delete ${t.name}`}>
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Infrastructure */}
      <section className="mt-8">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-navy-950">
          <Building2 className="h-5 w-5" /> Emergency infrastructure
        </h2>
        {infrastructure.loading && <Skeleton className="h-40" />}
        {infrastructure.error && (
          <p className="text-sm text-red-600">Infrastructure unavailable: {infrastructure.error}</p>
        )}
        {infrastructure.data && infrastructure.data.length === 0 && (
          <EmptyState title="No infrastructure records" description="Rescue centres and hospitals will appear here once registered." />
        )}
        {infrastructure.data && infrastructure.data.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Registry</CardTitle>
              <CardDescription>
                Rows marked “sample” are placeholder coordinates pending authoritative registries.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-navy-950 text-left text-white">
                      <th className="px-4 py-3 font-semibold">Facility</th>
                      <th className="px-4 py-3 font-semibold">Type</th>
                      <th className="px-4 py-3 font-semibold">District</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold">Contact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {infrastructure.data.map((f) => (
                      <tr key={f.id} className="border-b border-slate-100 last:border-0">
                        <td className="px-4 py-3 font-medium text-navy-950">
                          {f.name}
                          {f.is_sample_data && (
                            <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-slate-500">
                              sample
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-slate-600">{f.type.replace(/_/g, " ")}</td>
                        <td className="px-4 py-3 text-slate-600">{f.district_name ?? "—"}</td>
                        <td className="px-4 py-3">
                          <Badge variant={f.operational_status === "operational" ? "low" : "warning"}>
                            {f.operational_status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{f.contact_phone ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </section>
    </DashboardShell>
  );
}
