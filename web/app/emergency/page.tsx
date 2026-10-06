"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  PhoneCall,
  Siren,
  Tent,
  HeartPulse,
  LifeBuoy,
  MapPin,
  Loader2,
  AlertTriangle,
  Navigation,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  publicApi,
  RESOURCE_COLORS,
  type EmergencyContact,
  type GeoJSONFeatureCollection,
} from "@/lib/api/public";

/** Nationally verified emergency numbers shown statically on every load. */
const HOTLINES = [
  { number: "1122", label: "Rescue 1122", note: "Fire, rescue & ambulance — nationwide" },
  { number: "1736", label: "PDMA Sindh", note: "Provincial disaster management helpline" },
  { number: "911", label: "National emergency", note: "National emergency helpline" },
];

interface ShelterPoint {
  name: string;
  district: string | null;
  capacity: number | null;
  phone: string | null;
  sample: boolean;
  lng: number | null;
  lat: number | null;
}

/** Great-circle distance in kilometres between two WGS84 points. */
function haversineKm(aLat: number, aLng: number, bLat: number, bLng: number): number {
  const r = 6371;
  const dLat = ((bLat - aLat) * Math.PI) / 180;
  const dLng = ((bLng - aLng) * Math.PI) / 180;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((aLat * Math.PI) / 180) *
      Math.cos((bLat * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(s));
}

/**
 * Emergency help page — no login required. Verified hotlines, the live
 * emergency contact directory (filterable by district), and a shelter
 * finder backed by GET /public/emergency-contacts and
 * GET /public/map/resources?type=shelter.
 */
export default function EmergencyPage() {
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [shelters, setShelters] = useState<ShelterPoint[]>([]);
  const [district, setDistrict] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [userLoc, setUserLoc] = useState<{ lat: number; lng: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [locError, setLocError] = useState<string | null>(null);

  const useMyLocation = () => {
    if (!("geolocation" in navigator)) {
      setLocError("Location is not available on this device.");
      return;
    }
    setLocating(true);
    setLocError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLoc({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocError("Could not get your location. Showing district order instead.");
        setLocating(false);
      },
      { timeout: 10000 },
    );
  };

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      publicApi.emergencyContacts(),
      publicApi.resources("shelter"),
    ])
      .then(([c, geo]: [EmergencyContact[], GeoJSONFeatureCollection]) => {
        if (cancelled) return;
        setContacts(c);
        setShelters(
          geo.features.map((f) => {
            const coords =
              f.geometry?.type === "Point" && Array.isArray(f.geometry.coordinates)
                ? (f.geometry.coordinates as number[])
                : null;
            return {
              name: String(f.properties.name ?? "Shelter"),
              district: (f.properties.district_name as string) ?? null,
              capacity: (f.properties.capacity as number) ?? null,
              phone: (f.properties.contact_phone as string) ?? null,
              sample: f.properties.is_sample_data === true,
              lng: coords && coords.length >= 2 ? coords[0] : null,
              lat: coords && coords.length >= 2 ? coords[1] : null,
            };
          }),
        );
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const districts = useMemo(() => {
    const set = new Set<string>();
    for (const c of contacts) if (c.district_name) set.add(c.district_name);
    for (const s of shelters) if (s.district) set.add(s.district);
    return [...set].sort();
  }, [contacts, shelters]);

  const filteredContacts = district
    ? contacts.filter((c) => c.district_name === district)
    : contacts;
  const filteredShelters = useMemo(() => {
    const base = district ? shelters.filter((s) => s.district === district) : shelters;
    if (!userLoc) return base;
    return [...base].sort((a, b) => {
      const da =
        a.lat != null && a.lng != null
          ? haversineKm(userLoc.lat, userLoc.lng, a.lat, a.lng)
          : Number.POSITIVE_INFINITY;
      const db =
        b.lat != null && b.lng != null
          ? haversineKm(userLoc.lat, userLoc.lng, b.lat, b.lng)
          : Number.POSITIVE_INFINITY;
      return da - db;
    });
  }, [shelters, district, userLoc]);

  const shelterDistance = (s: ShelterPoint): number | null =>
    userLoc && s.lat != null && s.lng != null
      ? haversineKm(userLoc.lat, userLoc.lng, s.lat, s.lng)
      : null;

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        <div className="rounded-2xl bg-red-700 p-6 text-white sm:p-8">
          <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-red-100">
            <Siren className="h-4 w-4" /> Emergency help
          </p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
            In danger right now? Call first.
          </h1>
          <p className="mt-2 max-w-2xl text-red-100">
            If water is rising around you, call a rescue helpline immediately —
            do not wait for this page to load.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {HOTLINES.map((h) => (
              <a
                key={h.number}
                href={`tel:${h.number}`}
                className="flex items-center gap-3 rounded-xl bg-white/10 p-4 backdrop-blur transition-colors hover:bg-white/20"
              >
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white text-red-700">
                  <PhoneCall className="h-5 w-5" />
                </span>
                <span>
                  <span className="block text-2xl font-extrabold tracking-tight">
                    {h.number}
                  </span>
                  <span className="block text-xs text-red-100">
                    {h.label} — {h.note}
                  </span>
                </span>
              </a>
            ))}
          </div>
        </div>

        {/* District filter */}
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
          <label htmlFor="district-filter" className="text-sm font-semibold text-navy-950">
            Show resources for
          </label>
          <select
            id="district-filter"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm text-navy-950 focus:border-brand-500 focus:outline-none sm:w-64"
          >
            <option value="">All districts</option>
            {districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={useMyLocation}
            disabled={locating}
            title="Sort shelters by distance from your current location"
          >
            {locating ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Navigation className="h-4 w-4" />
            )}
            {userLoc ? "Nearest first ✓" : "Use my location"}
          </Button>
          <Link href="/map" className="sm:ml-auto">
            <Button variant="outline" size="sm">
              <MapPin className="h-4 w-4" /> View on map
            </Button>
          </Link>
        </div>
        {locError && (
          <p className="mt-2 text-xs text-amber-700">{locError}</p>
        )}

        {loading && (
          <div className="mt-8 flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white p-10 text-sm text-slate-600">
            <Loader2 className="h-5 w-5 animate-spin text-brand-700" />
            Loading emergency resources…
          </div>
        )}
        {error && (
          <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
            <p className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              The live directory could not be loaded. The helplines above work
              without internet data — call <strong>1122</strong> in an
              emergency.
            </p>
          </div>
        )}

        {!loading && !error && (
          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            {/* Emergency contacts */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PhoneCall className="h-5 w-5 text-red-700" />
                  Emergency contacts
                  <Badge variant="info" className="ml-1">
                    {filteredContacts.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {filteredContacts.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No directory contacts listed for this district yet. Use the
                    helplines above.
                  </p>
                ) : (
                  <ul className="divide-y divide-slate-100">
                    {filteredContacts.map((c) => (
                      <li key={c.id} className="flex items-center justify-between gap-3 py-3">
                        <div>
                          <p className="text-sm font-semibold text-navy-950">
                            {c.name ?? c.organization}
                          </p>
                          <p className="text-xs text-slate-500">
                            {c.organization}
                            {c.district_name ? ` · ${c.district_name}` : ""}
                          </p>
                        </div>
                        <a
                          href={`tel:${c.phone.replace(/[^+\d]/g, "")}`}
                          className="flex shrink-0 items-center gap-1.5 rounded-lg bg-red-700 px-3 py-2 text-sm font-bold text-white hover:bg-red-800"
                        >
                          <PhoneCall className="h-4 w-4" />
                          {c.phone}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Shelter finder */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Tent className="h-5 w-5" style={{ color: RESOURCE_COLORS.shelter }} />
                  Shelter finder
                  <Badge variant="info" className="ml-1">
                    {filteredShelters.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {filteredShelters.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No shelters listed for this district yet. Contact{" "}
                    <strong>PDMA Sindh 1736</strong> for the nearest relief camp.
                  </p>
                ) : (
                  <ul className="divide-y divide-slate-100">
                    {filteredShelters.map((s, i) => (
                      <li key={i} className="py-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-navy-950">
                              {s.name}
                            </p>
                            <p className="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-slate-500">
                              {shelterDistance(s) != null && (
                                <span className="font-semibold text-brand-700">
                                  ≈ {shelterDistance(s)!.toFixed(1)} km away
                                </span>
                              )}
                              {s.district && (
                                <span className="flex items-center gap-1">
                                  <MapPin className="h-3 w-3" /> {s.district}
                                </span>
                              )}
                              {s.capacity != null && (
                                <span>Capacity: {s.capacity}</span>
                              )}
                              {s.phone && (
                                <a
                                  href={`tel:${s.phone.replace(/[^+\d]/g, "")}`}
                                  className="font-semibold text-brand-700 hover:underline"
                                >
                                  {s.phone}
                                </a>
                              )}
                            </p>
                          </div>
                        </div>
                        {s.sample && (
                          <p className="mt-1 text-[11px] text-amber-700">
                            Illustrative location — confirm with local
                            authorities before travelling.
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Nearby resources explainer */}
        {!loading && !error && (
          <Card className="mt-6">
            <CardContent className="grid gap-4 p-6 sm:grid-cols-3">
              <div className="flex items-start gap-3">
                <HeartPulse
                  className="mt-0.5 h-5 w-5 shrink-0"
                  style={{ color: RESOURCE_COLORS.hospital }}
                />
                <div>
                  <p className="text-sm font-semibold text-navy-950">Hospitals</p>
                  <p className="text-xs text-slate-600">
                    Find the nearest hospital on the{" "}
                    <Link href="/map" className="font-semibold text-brand-700 hover:underline">
                      relief map
                    </Link>{" "}
                    — toggle the Hospitals layer.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <LifeBuoy
                  className="mt-0.5 h-5 w-5 shrink-0"
                  style={{ color: RESOURCE_COLORS.rescue_center }}
                />
                <div>
                  <p className="text-sm font-semibold text-navy-950">Rescue centres</p>
                  <p className="text-xs text-slate-600">
                    Rescue centres coordinate boats and evacuation — call{" "}
                    <strong>1122</strong> to request rescue.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Tent
                  className="mt-0.5 h-5 w-5 shrink-0"
                  style={{ color: RESOURCE_COLORS.shelter }}
                />
                <div>
                  <p className="text-sm font-semibold text-navy-950">Before you travel</p>
                  <p className="text-xs text-slate-600">
                    Never walk or drive through flood water. Take the highest
                    available route and inform family where you are going.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
      <Footer />
    </div>
  );
}
