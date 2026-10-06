"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Loader2,
  MapPin,
  Navigation,
  PhoneCall,
  Tent,
  TriangleAlert,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  publicApi,
  type EmergencyContact,
  type GeoJSONFeatureCollection,
  type SituationResponse,
} from "@/lib/api/public";
import { formatProbability } from "@/lib/format";
import { haversineKm, useGeolocation } from "@/lib/geo";

interface DistrictPoint {
  name: string;
  lat: number;
  lng: number;
}

interface ShelterPoint {
  name: string;
  district: string | null;
  phone: string | null;
  lat: number;
  lng: number;
}

function toDistrictPoints(fc: GeoJSONFeatureCollection): DistrictPoint[] {
  const pts: DistrictPoint[] = [];
  for (const f of fc.features) {
    const g = f.geometry;
    if (g?.type === "Point" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
      const name = String(f.properties?.district_name ?? "");
      if (!name || pts.some((p) => p.name === name)) continue;
      pts.push({ name, lng: (g.coordinates as number[])[0], lat: (g.coordinates as number[])[1] });
    }
  }
  return pts;
}

function toShelterPoints(fc: GeoJSONFeatureCollection): ShelterPoint[] {
  const pts: ShelterPoint[] = [];
  for (const f of fc.features) {
    const g = f.geometry;
    if (g?.type === "Point" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
      pts.push({
        name: String(f.properties?.name ?? "Shelter"),
        district: (f.properties?.district_name as string) ?? null,
        phone: (f.properties?.contact_phone as string) ?? null,
        lng: (g.coordinates as number[])[0],
        lat: (g.coordinates as number[])[1],
      });
    }
  }
  return pts;
}

const levelVariant = (l: string) =>
  l === "HIGH" ? "high" : l === "MEDIUM" ? "medium" : "low";

/**
 * Location-based public experience: "Use my location" detects the
 * citizen's position (stays on-device), matches the nearest monitored
 * district, and shows their risk level, nearest shelter, and rescue
 * contacts — all from the live public endpoints.
 */
export function MyLocationCard() {
  const { loc, locating, error: locError, request } = useGeolocation();
  const [zones, setZones] = useState<GeoJSONFeatureCollection | null>(null);
  const [situation, setSituation] = useState<SituationResponse | null>(null);
  const [shelters, setShelters] = useState<GeoJSONFeatureCollection | null>(null);
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      publicApi.riskZones(),
      publicApi.situation().catch(() => null),
      publicApi.resources("shelter").catch(() => null),
      publicApi.emergencyContacts().catch(() => []),
    ])
      .then(([z, s, sh, c]) => {
        if (cancelled) return;
        setZones(z);
        setSituation(s);
        setShelters(sh);
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

  const districtPoints = useMemo(() => (zones ? toDistrictPoints(zones) : []), [zones]);
  const shelterPoints = useMemo(
    () => (shelters ? toShelterPoints(shelters) : []),
    [shelters],
  );

  const nearest = useMemo(() => {
    if (!loc || districtPoints.length === 0) return null;
    let best: (DistrictPoint & { distanceKm: number }) | null = null;
    for (const p of districtPoints) {
      const d = haversineKm(loc.lat, loc.lng, p.lat, p.lng);
      if (!best || d < best.distanceKm) best = { ...p, distanceKm: d };
    }
    return best;
  }, [loc, districtPoints]);

  const risk = useMemo(() => {
    if (!nearest) return null;
    return (
      situation?.latest_predictions.find(
        (p) => p.district_name.toLowerCase() === nearest.name.toLowerCase(),
      ) ?? null
    );
  }, [nearest, situation]);

  const nearestShelter = useMemo(() => {
    if (!loc || shelterPoints.length === 0) return null;
    let best: (ShelterPoint & { distanceKm: number }) | null = null;
    for (const s of shelterPoints) {
      const d = haversineKm(loc.lat, loc.lng, s.lat, s.lng);
      if (!best || d < best.distanceKm) best = { ...s, distanceKm: d };
    }
    return best;
  }, [loc, shelterPoints]);

  const districtContacts = useMemo(() => {
    if (!nearest) return contacts.slice(0, 3);
    const local = contacts.filter(
      (c) =>
        c.district_name?.toLowerCase() === nearest.name.toLowerCase(),
    );
    return (local.length > 0 ? local : contacts).slice(0, 3);
  }, [nearest, contacts]);

  return (
    <Card className="overflow-hidden border-navy-200">
      <CardHeader className="bg-navy-950 text-white">
        <CardTitle className="flex items-center gap-2 text-base">
          <Navigation className="h-5 w-5" /> Your location, your risk
        </CardTitle>
      </CardHeader>
      <CardContent className="p-5">
        {!loc && (
          <div className="text-center">
            <p className="text-sm text-slate-600">
              Share your location to find your district&apos;s current risk
              level, the nearest shelter, and rescue contacts. Your coordinates
              never leave this device.
            </p>
            <Button
              variant="brand"
              className="mt-4"
              onClick={request}
              disabled={locating || loading}
            >
              {locating || loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <MapPin className="h-4 w-4" />
              )}
              Use my location
            </Button>
            {locError && (
              <p className="mt-2 text-xs text-amber-700">{locError}</p>
            )}
          </div>
        )}

        {loc && nearest && (
          <div className="animate-fade-in-up space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Your location
                </p>
                <p className="text-xl font-extrabold text-navy-950">
                  {nearest.name} District
                </p>
                <p className="text-xs text-slate-500">
                  nearest monitored district · {nearest.distanceKm.toFixed(1)} km from centre
                </p>
              </div>
              {risk ? (
                <Badge variant={levelVariant(risk.risk_level) as "low" | "medium" | "high"} className="text-sm">
                  {risk.risk_level} · {formatProbability(risk.probability)}
                </Badge>
              ) : (
                <Badge variant="outline">Risk data unavailable</Badge>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-500">
                  <Tent className="h-3.5 w-3.5" /> Nearest shelter
                </p>
                {nearestShelter ? (
                  <>
                    <p className="mt-1 font-bold text-navy-950">
                      {nearestShelter.name}
                    </p>
                    <p className="text-sm text-slate-600">
                      {nearestShelter.distanceKm.toFixed(1)} km away
                      {nearestShelter.district ? ` · ${nearestShelter.district}` : ""}
                    </p>
                    {nearestShelter.phone && (
                      <a
                        href={`tel:${nearestShelter.phone}`}
                        className="mt-1 inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-600"
                      >
                        <PhoneCall className="h-3.5 w-3.5" /> {nearestShelter.phone}
                      </a>
                    )}
                  </>
                ) : (
                  <p className="mt-1 text-sm text-slate-500">
                    No shelter coordinates on record — call Rescue 1122.
                  </p>
                )}
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-500">
                  <PhoneCall className="h-3.5 w-3.5" /> Emergency contacts
                </p>
                <a
                  href="tel:1122"
                  className="mt-1 flex items-center justify-between font-extrabold text-red-700"
                >
                  Rescue 1122 <span className="tracking-widest">1122</span>
                </a>
                {districtContacts.map((c) => (
                  <a
                    key={c.id}
                    href={`tel:${c.phone}`}
                    className="mt-1 flex items-center justify-between text-sm font-semibold text-navy-950 hover:text-brand-700"
                  >
                    <span className="truncate">{c.organization}</span>
                    <span className="ml-2 shrink-0">{c.phone}</span>
                  </a>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Link
                href={`/risk-check?district=${encodeURIComponent(nearest.name)}`}
                className="rounded-lg bg-navy-950 px-4 py-2 text-sm font-semibold text-white hover:bg-navy-800"
              >
                Full district assessment
              </Link>
              <Link
                href="/emergency"
                className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-navy-950 hover:border-navy-700"
              >
                <TriangleAlert className="h-4 w-4" /> Emergency help
              </Link>
              <button
                onClick={request}
                className="rounded-lg px-3 py-2 text-xs font-semibold text-slate-500 hover:text-navy-800"
              >
                Recheck location
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
