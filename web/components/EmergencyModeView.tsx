"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  BellRing,
  ChevronRight,
  LifeBuoy,
  Loader2,
  MapPin,
  Navigation,
  PhoneCall,
  Siren,
  Tent,
  X,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertCard } from "@/components/AlertCard";
import {
  publicApi,
  type EmergencyContact,
  type GeoJSONFeatureCollection,
  type SituationResponse,
} from "@/lib/api/public";
import type { AlertOut } from "@/lib/api/types";
import { formatProbability } from "@/lib/format";
import { haversineKm, nearestTo, useGeolocation } from "@/lib/geo";
import { cn } from "@/lib/utils";

const HOTLINES = [
  { number: "1122", label: "Rescue 1122", note: "Fire, rescue & ambulance" },
  { number: "1736", label: "PDMA Sindh", note: "Provincial disaster helpline" },
  { number: "911", label: "National emergency", note: "National helpline" },
];

interface ShelterPoint {
  name: string;
  district: string | null;
  capacity: number | null;
  phone: string | null;
  lat: number;
  lng: number;
}

function toShelters(fc: GeoJSONFeatureCollection): ShelterPoint[] {
  return fc.features
    .map((f) => {
      const coords =
        f.geometry?.type === "Point" && Array.isArray(f.geometry.coordinates)
          ? (f.geometry.coordinates as number[])
          : null;
      if (!coords || coords.length < 2) return null;
      return {
        name: String(f.properties.name ?? "Shelter"),
        district: (f.properties.district_name as string) ?? null,
        capacity: (f.properties.capacity as number) ?? null,
        phone: (f.properties.contact_phone as string) ?? null,
        lng: coords[0],
        lat: coords[1],
      } as ShelterPoint;
    })
    .filter((s): s is ShelterPoint => s !== null);
}

const SAFETY_NOW = [
  "Move to higher ground immediately when a warning is issued — do not wait.",
  "Never walk or drive through flowing water; 15 cm can knock you down.",
  "Turn off electricity and gas if water enters your home.",
  "Keep drinking water, dry food, medicines, and documents in a waterproof bag.",
  "Call Rescue 1122 for rescue — do not attempt crossings yourself.",
];

/**
 * Emergency Mode — an urgent-information-first view of the same live data.
 * Activated from the dashboard toggle; prioritises active alerts,
 * highest-risk districts, nearest shelters, rescue contacts, and
 * immediate safety instructions.
 */
export function EmergencyModeView({
  situation,
  alerts,
  onExit,
}: {
  situation: SituationResponse | null;
  alerts: AlertOut[];
  onExit: () => void;
}) {
  const [shelters, setShelters] = useState<ShelterPoint[]>([]);
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [loading, setLoading] = useState(true);
  const { loc, locating, error: locError, request } = useGeolocation();

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      publicApi.resources("shelter"),
      publicApi.emergencyContacts(),
    ])
      .then(([geo, c]) => {
        if (cancelled) return;
        setShelters(toShelters(geo));
        setContacts(c);
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const nearest = useMemo(
    () => (loc ? nearestTo(loc, shelters) : null),
    [loc, shelters],
  );

  const sortedShelters = useMemo(() => {
    if (!loc) return shelters.slice(0, 5);
    return shelters
      .map((s) => ({ ...s, distanceKm: haversineKm(loc.lat, loc.lng, s.lat, s.lng) }))
      .sort((a, b) => a.distanceKm - b.distanceKm)
      .slice(0, 5);
  }, [loc, shelters]);

  const highRisk = situation?.high_risk_districts ?? [];
  const emergencyAlerts = alerts.filter((a) => a.severity === "emergency");

  return (
    <div className="animate-fade-in-up space-y-6">
      {/* Mode banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-red-700 p-5 text-white shadow-lg">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white/15">
            <Siren className="h-6 w-6" />
          </span>
          <div>
            <p className="text-lg font-extrabold uppercase tracking-wider">
              Emergency mode
            </p>
            <p className="text-sm text-white/85">
              Urgent information first — alerts, risk, shelters, contacts.
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={onExit}
          className="border-white/40 bg-transparent text-white hover:bg-white/10 hover:text-white"
        >
          <X className="h-4 w-4" /> Exit emergency mode
        </Button>
      </div>

      {/* Current emergency alerts */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-bold text-navy-950">
          <BellRing className="h-5 w-5 text-red-700" /> Emergency alerts
        </h2>
        {emergencyAlerts.length === 0 ? (
          <Card>
            <CardContent className="p-5 text-sm text-slate-600">
              No emergency-severity alerts are active right now. Stay alert —
              conditions are monitored continuously.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {emergencyAlerts.map((a) => (
              <AlertCard key={a.id} alert={a} />
            ))}
          </div>
        )}
      </section>

      {/* Highest-risk districts */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-bold text-navy-950">
          <AlertTriangle className="h-5 w-5 text-red-700" /> Highest-risk districts
        </h2>
        {highRisk.length === 0 ? (
          <Card>
            <CardContent className="p-5 text-sm text-emerald-800">
              No district is currently at high risk.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {highRisk.map((d) => (
              <Card key={d.district_name} className="border-l-4 border-l-red-700">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <p className="text-lg font-extrabold text-navy-950">
                      {d.district_name}
                    </p>
                    <Badge variant="high">
                      HIGH · {formatProbability(d.probability)}
                    </Badge>
                  </div>
                  {d.recommended_actions.length > 0 && (
                    <ul className="mt-3 space-y-1.5 text-sm text-slate-700">
                      {d.recommended_actions.slice(0, 3).map((a) => (
                        <li key={a} className="flex gap-2">
                          <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                          {a}
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link
                      href={`/risk-check?district=${encodeURIComponent(d.district_name)}`}
                      className="rounded-lg bg-navy-950 px-3 py-1.5 text-xs font-semibold text-white hover:bg-navy-800"
                    >
                      Full assessment
                    </Link>
                    <Link
                      href="/emergency"
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-navy-950 hover:border-navy-700"
                    >
                      Find shelter
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Nearest shelters */}
      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 text-lg font-bold text-navy-950">
            <Tent className="h-5 w-5 text-navy-700" /> Nearest shelters
          </h2>
          <Button variant="outline" size="sm" onClick={request} disabled={locating}>
            {locating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Navigation className="h-4 w-4" />
            )}
            {loc ? "Location set — recalculate" : "Use my location"}
          </Button>
        </div>
        {locError && <p className="mb-2 text-xs text-amber-700">{locError}</p>}
        {loading ? (
          <p className="text-sm text-slate-500">Loading shelters…</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sortedShelters.map((s, i) => (
              <Card
                key={`${s.name}-${i}`}
                className={cn(i === 0 && loc && "border-2 border-navy-700")}
              >
                <CardContent className="p-4">
                  <p className="font-bold text-navy-950">{s.name}</p>
                  <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                    <MapPin className="h-3 w-3" />
                    {s.district ?? "—"}
                    {"distanceKm" in s && typeof s.distanceKm === "number" && (
                      <span className="ml-1 font-semibold text-navy-700">
                        · {s.distanceKm.toFixed(1)} km away
                      </span>
                    )}
                  </p>
                  {s.capacity != null && (
                    <p className="mt-1 text-xs text-slate-500">
                      Capacity: {s.capacity}
                    </p>
                  )}
                  {s.phone && (
                    <a
                      href={`tel:${s.phone}`}
                      className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-600"
                    >
                      <PhoneCall className="h-3 w-3" /> {s.phone}
                    </a>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        {nearest && loc && (
          <p className="mt-2 text-sm font-semibold text-navy-950">
            Closest to you: {nearest.name} — {nearest.distanceKm.toFixed(1)} km
          </p>
        )}
      </section>

      {/* Rescue contacts + safety instructions */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-l-4 border-l-red-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <PhoneCall className="h-5 w-5 text-red-700" /> Rescue contacts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {HOTLINES.map((h) => (
              <a
                key={h.number}
                href={`tel:${h.number}`}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 transition-colors hover:bg-red-50"
              >
                <span>
                  <span className="block font-bold text-navy-950">{h.label}</span>
                  <span className="text-xs text-slate-500">{h.note}</span>
                </span>
                <span className="text-xl font-extrabold tracking-wider text-red-700">
                  {h.number}
                </span>
              </a>
            ))}
            {contacts.slice(0, 3).map((c) => (
              <a
                key={c.id}
                href={`tel:${c.phone}`}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 transition-colors hover:bg-red-50"
              >
                <span>
                  <span className="block font-bold text-navy-950">
                    {c.organization}
                  </span>
                  <span className="text-xs text-slate-500">
                    {c.district_name ?? "All districts"}
                  </span>
                </span>
                <span className="font-bold text-navy-800">{c.phone}</span>
              </a>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <LifeBuoy className="h-5 w-5 text-navy-700" /> Safety instructions — act now
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              {SAFETY_NOW.map((s, i) => (
                <li key={s} className="flex gap-3 text-sm text-slate-700">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-navy-950 text-xs font-bold text-white">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{s}</span>
                </li>
              ))}
            </ol>
            <Link
              href="/learn"
              className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-600"
            >
              Full safety guide <ChevronRight className="h-4 w-4" />
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/** Standalone Emergency Mode toggle button for dashboard headers. */
export function EmergencyModeToggle({
  active,
  onToggle,
}: {
  active: boolean;
  onToggle: () => void;
}) {
  return (
    <Button
      onClick={onToggle}
      variant={active ? "outline" : "alert"}
      className={cn("gap-2 font-bold", !active && "shadow-lg")}
    >
      <Siren className="h-4 w-4" />
      {active ? "Exit emergency mode" : "Emergency mode"}
    </Button>
  );
}
