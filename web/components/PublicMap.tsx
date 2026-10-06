"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { Search, Layers, Loader2 } from "lucide-react";
import { publicApi, RISK_COLORS, RESOURCE_COLORS, type GeoJSONFeatureCollection, type SituationResponse } from "@/lib/api/public";
import { Badge } from "@/components/ui/badge";
import { formatProbability } from "@/lib/format";
import { cn } from "@/lib/utils";

type LayerKey = "risk" | "shelter" | "hospital" | "rescue_center" | "history";

const LAYER_META: { key: LayerKey; label: string; color: string }[] = [
  { key: "risk", label: "Flood risk zones", color: "#dc2626" },
  { key: "shelter", label: "Shelters", color: RESOURCE_COLORS.shelter },
  { key: "hospital", label: "Hospitals", color: RESOURCE_COLORS.hospital },
  { key: "rescue_center", label: "Rescue centres", color: RESOURCE_COLORS.rescue_center },
  { key: "history", label: "Historical floods", color: "#0ea5e9" },
];

const SEVERITY_COLOR: Record<string, string> = {
  Minor: "#fbbf24",
  Moderate: "#f59e0b",
  Severe: "#f97316",
  "Very severe": "#ef4444",
  Catastrophic: "#991b1b",
};

/** Small glyph for a contributing factor name from the situation feed. */
function factorIcon(factor: string): string {
  const f = factor.toLowerCase();
  if (f.includes("rain")) return "🌧";
  if (f.includes("river")) return "🌊";
  if (f.includes("vulnerab")) return "🏚";
  if (f.includes("temp")) return "🌡";
  if (f.includes("humid")) return "💧";
  if (f.includes("elev") || f.includes("terrain")) return "⛰";
  if (f.includes("hist") || f.includes("past")) return "📜";
  return "•";
}

/** Small glyph for a recommended action from the situation feed. */
function actionIcon(action: string): string {
  const a = action.toLowerCase();
  if (a.includes("evacuat")) return "⚠";
  if (a.includes("shelter")) return "🏠";
  if (a.includes("1122") || a.includes("contact") || a.includes("call"))
    return "📞";
  if (a.includes("monitor") || a.includes("alert")) return "🔔";
  return "→";
}

function prettyFactor(f: string): string {
  return f.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function FlyTo({ target }: { target: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.flyTo(target, 10, { duration: 1.2 });
  }, [target, map]);
  return null;
}

function FitInitial({ fc }: { fc: GeoJSONFeatureCollection | null }) {
  const map = useMap();
  useEffect(() => {
    if (!fc || fc.features.length === 0) return;
    try {
      const layer = L.geoJSON(fc as unknown as GeoJSON.GeoJsonObject);
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
    } catch {
      /* keep default view */
    }
  }, [fc, map]);
  return null;
}

interface Point {
  lat: number;
  lng: number;
  props: Record<string, unknown>;
}

function toPoints(fc: GeoJSONFeatureCollection | null): Point[] {
  if (!fc) return [];
  const pts: Point[] = [];
  for (const f of fc.features) {
    const g = f.geometry;
    if (g?.type === "Point" && Array.isArray(g.coordinates) && g.coordinates.length >= 2) {
      const [lng, lat] = g.coordinates as number[];
      pts.push({ lat, lng, props: f.properties ?? {} });
    }
  }
  return pts;
}

/**
 * Public GIS map for ordinary citizens: flood risk zones, shelters,
 * hospitals, rescue centres, and historical floods — with layer toggles,
 * district search, and information popups. All data from the
 * unauthenticated /public/map/* endpoints.
 */
export function PublicMap() {
  const searchParams = useSearchParams();
  // Deep-link support: /map?layer=history pre-enables the historical layer.
  // (Initialised lazily from the URL — no setState-in-effect needed.)
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>(() => ({
    risk: true,
    shelter: true,
    hospital: true,
    rescue_center: true,
    history: searchParams.get("layer") === "history",
  }));
  const [riskZones, setRiskZones] = useState<GeoJSONFeatureCollection | null>(null);
  const [resources, setResources] = useState<GeoJSONFeatureCollection | null>(null);
  const [history, setHistory] = useState<GeoJSONFeatureCollection | null>(null);
  const [situation, setSituation] = useState<SituationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");
  const [flyTarget, setFlyTarget] = useState<[number, number] | null>(null);
  const [searchMiss, setSearchMiss] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      publicApi.riskZones(),
      publicApi.resources(),
      publicApi.historicalFloods(),
      publicApi.situation().catch(() => null),
    ])
      .then(([rz, res, hist, sit]) => {
        if (cancelled) return;
        setRiskZones(rz);
        setResources(res);
        setHistory(hist);
        setSituation(sit);
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

  // Live assessment details (factors + recommended actions) keyed by district.
  const situationByDistrict = useMemo(() => {
    const m = new Map<
      string,
      { factors: string[]; actions: string[] }
    >();
    for (const d of situation?.high_risk_districts ?? []) {
      m.set(d.district_name.toLowerCase(), {
        factors: (d.top_factors ?? []).slice(0, 3).map((f) => f.feature),
        actions: (d.recommended_actions ?? []).slice(0, 3),
      });
    }
    return m;
  }, [situation]);

  const riskPoints = useMemo(() => toPoints(riskZones), [riskZones]);
  const resourcePoints = useMemo(() => toPoints(resources), [resources]);
  const historyPoints = useMemo(() => toPoints(history), [history]);

  const byType = useMemo(() => {
    const m: Record<string, Point[]> = { shelter: [], hospital: [], rescue_center: [], emergency_facility: [] };
    for (const p of resourcePoints) {
      const t = String(p.props.type ?? "");
      if (m[t]) m[t].push(p);
    }
    return m;
  }, [resourcePoints]);

  const search = () => {
    const q = query.trim().toLowerCase();
    if (!q) return;
    const hit = riskPoints.find((p) =>
      String(p.props.district_name ?? "").toLowerCase().includes(q),
    );
    if (hit) {
      setFlyTarget([hit.lat, hit.lng]);
      setSearchMiss(false);
    } else {
      setSearchMiss(true);
    }
  };

  const toggle = (key: LayerKey) =>
    setLayers((l) => ({ ...l, [key]: !l[key] }));

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center rounded-xl border border-slate-200 bg-slate-50">
        <Loader2 className="h-6 w-6 animate-spin text-brand-700" />
        <span className="ml-2 text-sm text-slate-600">Loading map layers…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-800">
        The map layers could not be loaded right now. Please try again later —
        in an emergency call <strong>Rescue 1122</strong>.
      </div>
    );
  }

  const riskColor = (p: Point) =>
    String(p.props.color ?? RISK_COLORS[String(p.props.risk_level ?? "LOW") as keyof typeof RISK_COLORS] ?? "#10b981");

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200">
      {/* Controls */}
      <div className="flex flex-col gap-3 border-b border-slate-200 bg-white p-3 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-2">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && search()}
              placeholder="Search a district, e.g. Dadu…"
              className="h-10 w-full rounded-lg border border-slate-300 pl-9 pr-3 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>
          <button
            onClick={search}
            className="h-10 shrink-0 rounded-lg bg-navy-950 px-4 text-sm font-semibold text-white hover:bg-navy-800"
          >
            Search
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Layers className="h-4 w-4 text-slate-500" />
          {LAYER_META.map((m) => (
            <button
              key={m.key}
              onClick={() => toggle(m.key)}
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                layers[m.key]
                  ? "border-navy-950 bg-navy-950 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:border-slate-400",
              )}
            >
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: m.color }}
              />
              {m.label}
            </button>
          ))}
        </div>
      </div>
      {searchMiss && (
        <p className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">
          No district matching “{query}” was found. Try another spelling.
        </p>
      )}

      {/* Map */}
      <MapContainer
        center={[27.0, 68.5]}
        zoom={7}
        scrollWheelZoom
        className="h-[62vh] w-full"
        style={{ zIndex: 0 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitInitial fc={riskZones} />
        <FlyTo target={flyTarget} />

        {layers.risk &&
          riskPoints.map((p, i) => {
            const name = String(p.props.district_name ?? "District");
            const level = String(p.props.risk_level ?? "—").toUpperCase();
            const prob =
              typeof p.props.probability === "number"
                ? formatProbability(p.props.probability)
                : "—";
            const detail = situationByDistrict.get(name.toLowerCase());
            const badgeVariant =
              level === "HIGH" ? "high" : level === "MEDIUM" ? "medium" : "low";
            return (
              <CircleMarker
                key={`risk-${i}`}
                center={[p.lat, p.lng]}
                radius={16}
                pathOptions={{
                  color: riskColor(p),
                  fillColor: riskColor(p),
                  fillOpacity: 0.35,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="min-w-[230px] max-w-[260px]">
                    <div className="flex items-center justify-between gap-2">
                      <strong className="text-sm text-navy-950">
                        {name} District
                      </strong>
                      <Badge variant={badgeVariant}>{level} RISK</Badge>
                    </div>
                    <div className="mt-2 rounded-lg bg-slate-50 px-3 py-2">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        Probability
                      </p>
                      <p className="text-2xl font-extrabold text-navy-950">
                        {prob}
                      </p>
                    </div>
                    {detail && detail.factors.length > 0 && (
                      <div className="mt-2">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                          Main factors
                        </p>
                        <ul className="mt-1 space-y-0.5 text-xs text-slate-700">
                          {detail.factors.map((f) => (
                            <li key={f} className="flex items-center gap-1.5">
                              <span>{factorIcon(f)}</span>
                              {prettyFactor(f)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {detail && detail.actions.length > 0 && (
                      <div className="mt-2">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                          Recommended actions
                        </p>
                        <ul className="mt-1 space-y-0.5 text-xs text-slate-700">
                          {detail.actions.map((a) => (
                            <li key={a} className="flex items-start gap-1.5">
                              <span>{actionIcon(a)}</span>
                              <span>{a}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      <Link
                        href={`/risk-check?district=${encodeURIComponent(name)}`}
                        className="rounded-md bg-navy-950 px-2.5 py-1.5 text-[11px] font-semibold text-white hover:bg-navy-800"
                      >
                        Risk assessment
                      </Link>
                      <Link
                        href="/emergency"
                        className="rounded-md border border-slate-300 px-2.5 py-1.5 text-[11px] font-semibold text-navy-950 hover:border-navy-700"
                      >
                        Find shelter
                      </Link>
                      <Link
                        href="/emergency"
                        className="rounded-md border border-slate-300 px-2.5 py-1.5 text-[11px] font-semibold text-navy-950 hover:border-navy-700"
                      >
                        Emergency contact
                      </Link>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

        {(["shelter", "hospital", "rescue_center"] as const).map(
          (t) =>
            layers[t] &&
            byType[t].map((p, i) => (
              <CircleMarker
                key={`${t}-${i}`}
                center={[p.lat, p.lng]}
                radius={8}
                pathOptions={{
                  color: RESOURCE_COLORS[t],
                  fillColor: RESOURCE_COLORS[t],
                  fillOpacity: 0.85,
                  weight: 2,
                }}
              >
                <Popup>
                  <div style={{ minWidth: 190 }}>
                    <strong style={{ fontSize: 14 }}>
                      {String(p.props.name ?? "Facility")}
                    </strong>
                    <br />
                    <span style={{ textTransform: "capitalize" }}>
                      {t.replace("_", " ")}
                    </span>
                    {p.props.district_name != null && (
                      <>
                        {" · "}
                        {String(p.props.district_name)}
                      </>
                    )}
                    <br />
                    {p.props.contact_phone != null && (
                      <>
                        Phone: <strong>{String(p.props.contact_phone)}</strong>
                        <br />
                      </>
                    )}
                    {p.props.capacity != null && (
                      <>
                        Capacity: {String(p.props.capacity)}
                        <br />
                      </>
                    )}
                    Status: {String(p.props.operational_status ?? "—")}
                    {p.props.is_sample_data === true && (
                      <div style={{ fontSize: 11, color: "#b45309", marginTop: 4 }}>
                        Illustrative location — confirm with local authorities.
                      </div>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            )),
        )}

        {layers.history &&
          historyPoints.map((p, i) => {
            const sev = String(p.props.severity_label ?? "Moderate");
            const color = SEVERITY_COLOR[sev] ?? "#0ea5e9";
            return (
              <CircleMarker
                key={`hist-${i}`}
                center={[p.lat, p.lng]}
                radius={6}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.6, weight: 1 }}
              >
                <Popup>
                  <div style={{ minWidth: 180 }}>
                    <strong style={{ fontSize: 14 }}>
                      {String(p.props.district_name ?? "District")} — {String(p.props.year ?? "")}
                    </strong>
                    <br />
                    Severity: <strong>{sev}</strong>
                    <br />
                    {p.props.affected_population != null && (
                      <>
                        Affected: {Number(p.props.affected_population).toLocaleString()}
                        <br />
                      </>
                    )}
                    {p.props.source != null && (
                      <span style={{ fontSize: 11, color: "#64748b" }}>
                        Source: {String(p.props.source)}
                      </span>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
      </MapContainer>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-5 gap-y-2 border-t border-slate-200 bg-white px-4 py-3 text-xs text-slate-600">
        <span className="font-semibold text-navy-950">Legend:</span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: "#dc2626" }} /> High risk
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: "#f59e0b" }} /> Medium risk
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: "#16a34a" }} /> Low risk
        </span>
        {LAYER_META.slice(1, 4).map((m) => (
          <span key={m.key} className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full" style={{ backgroundColor: m.color }} />
            {m.label}
          </span>
        ))}
      </div>
    </div>
  );
}
