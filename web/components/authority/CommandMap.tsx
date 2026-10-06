"use client";

import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { Layers, Loader2 } from "lucide-react";
import { adminApi, gisApi, incidentsApi, resourcesApi, weatherApi } from "@/lib/api/endpoints";
import type { GeoJSONFeatureCollection, ShelterResource, ResponseTeam, WeatherLatest } from "@/lib/api/types";
import { formatProbability } from "@/lib/format";
import { cn } from "@/lib/utils";

type LayerKey = "risk" | "incidents" | "reports" | "shelters" | "teams" | "rainfall";

const LAYER_META: { key: LayerKey; label: string; color: string }[] = [
  { key: "risk", label: "Risk zones", color: "#dc2626" },
  { key: "incidents", label: "Active incidents", color: "#b45309" },
  { key: "reports", label: "Field reports", color: "#7c3aed" },
  { key: "shelters", label: "Shelters", color: "#15803d" },
  { key: "teams", label: "Response teams", color: "#0ea5e9" },
  { key: "rainfall", label: "Rainfall data", color: "#0284c7" },
];

const RISK_COLORS: Record<string, string> = { HIGH: "#dc2626", MEDIUM: "#f59e0b", LOW: "#16a34a" };
const INCIDENT_COLORS: Record<string, string> = {
  detected: "#dc2626",
  verified: "#ea580c",
  response_started: "#f59e0b",
  resolved: "#16a34a",
};
const REPORT_COLORS: Record<string, string> = {
  pending: "#7c3aed",
  verified: "#0ea5e9",
  rejected: "#64748b",
  resolved: "#16a34a",
};

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
      if (lat === 0 && lng === 0) continue; // skip fallback coordinates
      pts.push({ lat, lng, props: (f.properties ?? {}) as Record<string, unknown> });
    }
  }
  return pts;
}

function FitInitial({ pts }: { pts: Point[] }) {
  const map = useMap();
  useEffect(() => {
    if (pts.length === 0) return;
    try {
      const bounds = L.latLngBounds(pts.map((p) => [p.lat, p.lng] as [number, number]));
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.2));
    } catch {
      /* keep default view */
    }
  }, [pts, map]);
  return null;
}

function Prop({ k, v }: { k: string; v: unknown }) {
  if (v == null || v === "") return null;
  return (
    <p className="text-xs text-slate-600">
      <span className="font-semibold">{k}: </span>
      {String(v)}
    </p>
  );
}

/**
 * Authority-only command map: risk zones, active incidents, field reports,
 * shelters and response teams — with layer toggles. All data from the
 * authenticated command-center endpoints.
 */
export function CommandMap() {
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    risk: true,
    incidents: true,
    reports: true,
    shelters: true,
    teams: true,
    rainfall: false,
  });
  const [risk, setRisk] = useState<GeoJSONFeatureCollection | null>(null);
  const [incidents, setIncidents] = useState<GeoJSONFeatureCollection | null>(null);
  const [reports, setReports] = useState<GeoJSONFeatureCollection | null>(null);
  const [shelters, setShelters] = useState<ShelterResource[]>([]);
  const [teams, setTeams] = useState<ResponseTeam[]>([]);
  const [weather, setWeather] = useState<WeatherLatest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      gisApi.riskLayer(),
      incidentsApi.map(true),
      adminApi.reportsMap(),
      resourcesApi.shelters(),
      resourcesApi.teams(),
    ])
      .then(([rz, inc, rep, sh, tm]) => {
        if (cancelled) return;
        setRisk(rz);
        setIncidents(inc);
        setReports(rep);
        setShelters(sh);
        setTeams(tm);
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      });
    // Rainfall observations load independently — the map stays usable
    // if the weather feed is unavailable.
    weatherApi
      .latest()
      .then((w) => {
        if (!cancelled) setWeather(w);
      })
      .catch(() => {
        /* rainfall layer stays empty */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const riskPoints = useMemo(() => toPoints(risk), [risk]);
  const incidentPoints = useMemo(() => toPoints(incidents), [incidents]);
  const reportPoints = useMemo(() => toPoints(reports), [reports]);
  const shelterPoints: Point[] = useMemo(
    () =>
      shelters
        .filter((s) => s.latitude != null && s.longitude != null)
        .map((s) => ({
          lat: s.latitude as number,
          lng: s.longitude as number,
          props: {
            kind: "shelter",
            name: s.name,
            district: s.district_name,
            occupancy: s.capacity != null ? `${s.current_occupancy}/${s.capacity}` : String(s.current_occupancy),
            status: s.status,
          },
        })),
    [shelters],
  );
  const teamPoints: Point[] = useMemo(
    () =>
      teams
        .filter((t) => t.latitude != null && t.longitude != null)
        .map((t) => ({
          lat: t.latitude as number,
          lng: t.longitude as number,
          props: {
            kind: "team",
            name: t.name,
            type: t.team_type,
            status: t.status,
            district: t.district_name,
          },
        })),
    [teams],
  );

  const allPoints = useMemo(
    () => [...riskPoints, ...incidentPoints, ...reportPoints, ...shelterPoints, ...teamPoints],
    [riskPoints, incidentPoints, reportPoints, shelterPoints, teamPoints],
  );

  // Rainfall layer: join the latest weather observations (by district name)
  // onto the risk-zone centroids so each district gets a rainfall marker.
  const rainfallPoints: Point[] = useMemo(() => {
    const centroidByDistrict = new Map<string, { lat: number; lng: number }>();
    for (const p of riskPoints) {
      const name = String(p.props.district_name ?? "").toLowerCase();
      if (name && !centroidByDistrict.has(name)) {
        centroidByDistrict.set(name, { lat: p.lat, lng: p.lng });
      }
    }
    return weather
      .filter((w) => w.rainfall_mm != null)
      .map((w) => {
        const c = centroidByDistrict.get(w.district_name.toLowerCase());
        if (!c) return null;
        return {
          lat: c.lat,
          lng: c.lng,
          props: {
            kind: "rainfall",
            district_name: w.district_name,
            rainfall_mm: w.rainfall_mm,
            temperature_c: w.temperature_c,
            humidity_pct: w.humidity_pct,
            observed_at: w.observed_at,
            source: w.source,
          },
        } as Point;
      })
      .filter((p): p is Point => p !== null);
  }, [weather, riskPoints]);

  if (loading) {
    return (
      <div className="flex h-[62vh] items-center justify-center rounded-xl border border-slate-200 bg-white">
        <Loader2 className="h-6 w-6 animate-spin text-navy-600" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="flex h-[62vh] items-center justify-center rounded-xl border border-slate-200 bg-white p-8 text-center">
        <p className="text-sm text-red-600">Command map data unavailable. Check the backend connection.</p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200">
      <MapContainer
        center={[27.0, 68.0]}
        zoom={7}
        scrollWheelZoom
        className="h-[62vh] w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitInitial pts={allPoints} />

        {layers.risk &&
          riskPoints.map((p, i) => (
            <CircleMarker
              key={`risk-${i}`}
              center={[p.lat, p.lng]}
              radius={10}
              pathOptions={{
                color: RISK_COLORS[String(p.props.risk_level)] ?? "#64748b",
                fillColor: RISK_COLORS[String(p.props.risk_level)] ?? "#64748b",
                fillOpacity: 0.35,
                weight: 2,
              }}
            >
              <Popup>
                <p className="text-sm font-bold">{String(p.props.district_name ?? "District")}</p>
                <Prop k="Risk" v={p.props.risk_level} />
                <Prop k="Probability" v={typeof p.props.probability === "number" ? formatProbability(p.props.probability as number) : undefined} />
                <Prop k="Model" v={p.props.model_version} />
              </Popup>
            </CircleMarker>
          ))}

        {layers.incidents &&
          incidentPoints.map((p, i) => (
            <CircleMarker
              key={`inc-${i}`}
              center={[p.lat, p.lng]}
              radius={9}
              pathOptions={{
                color: INCIDENT_COLORS[String(p.props.status)] ?? "#64748b",
                fillColor: INCIDENT_COLORS[String(p.props.status)] ?? "#64748b",
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Popup>
                <p className="text-sm font-bold">{String(p.props.title ?? "Incident")}</p>
                <Prop k="Status" v={String(p.props.status).replace(/_/g, " ")} />
                <Prop k="Severity" v={p.props.severity} />
                <Prop k="District" v={p.props.district_name} />
              </Popup>
            </CircleMarker>
          ))}

        {layers.reports &&
          reportPoints.map((p, i) => (
            <CircleMarker
              key={`rep-${i}`}
              center={[p.lat, p.lng]}
              radius={7}
              pathOptions={{
                color: REPORT_COLORS[String(p.props.status)] ?? "#64748b",
                fillColor: REPORT_COLORS[String(p.props.status)] ?? "#64748b",
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Popup>
                <p className="text-sm font-bold">{String(p.props.district_name ?? "Report")}</p>
                <Prop k="Category" v={String(p.props.category ?? "").replace(/_/g, " ")} />
                <Prop k="Status" v={p.props.status} />
                <Prop k="Priority" v={p.props.priority} />
                <Prop k="Detail" v={p.props.description} />
              </Popup>
            </CircleMarker>
          ))}

        {layers.shelters &&
          shelterPoints.map((p, i) => (
            <CircleMarker
              key={`sh-${i}`}
              center={[p.lat, p.lng]}
              radius={7}
              pathOptions={{ color: "#15803d", fillColor: "#15803d", fillOpacity: 0.6, weight: 2 }}
            >
              <Popup>
                <p className="text-sm font-bold">{String(p.props.name)}</p>
                <Prop k="Occupancy" v={p.props.occupancy} />
                <Prop k="Status" v={p.props.status} />
                <Prop k="District" v={p.props.district} />
              </Popup>
            </CircleMarker>
          ))}

        {layers.teams &&
          teamPoints.map((p, i) => (
            <CircleMarker
              key={`tm-${i}`}
              center={[p.lat, p.lng]}
              radius={7}
              pathOptions={{ color: "#0ea5e9", fillColor: "#0ea5e9", fillOpacity: 0.6, weight: 2 }}
            >
              <Popup>
                <p className="text-sm font-bold">{String(p.props.name)}</p>
                <Prop k="Type" v={p.props.type} />
                <Prop k="Status" v={p.props.status} />
                <Prop k="District" v={p.props.district} />
              </Popup>
            </CircleMarker>
          ))}

        {layers.rainfall &&
          rainfallPoints.map((p, i) => {
            const mm = Number(p.props.rainfall_mm ?? 0);
            const radius = Math.min(22, 6 + mm / 4);
            return (
              <CircleMarker
                key={`rf-${i}`}
                center={[p.lat, p.lng]}
                radius={radius}
                pathOptions={{ color: "#0284c7", fillColor: "#0284c7", fillOpacity: 0.45, weight: 2 }}
              >
                <Popup>
                  <p className="text-sm font-bold">
                    🌧 {String(p.props.district_name)} — rainfall
                  </p>
                  <Prop k="Rainfall (24h)" v={`${mm.toFixed(1)} mm`} />
                  <Prop
                    k="Temperature"
                    v={p.props.temperature_c != null ? `${Number(p.props.temperature_c).toFixed(1)} °C` : undefined}
                  />
                  <Prop
                    k="Humidity"
                    v={p.props.humidity_pct != null ? `${Number(p.props.humidity_pct).toFixed(0)}%` : undefined}
                  />
                  <Prop
                    k="Observed"
                    v={
                      p.props.observed_at
                        ? new Date(String(p.props.observed_at)).toLocaleString("en-PK", {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })
                        : undefined
                    }
                  />
                  <Prop k="Source" v={p.props.source} />
                </Popup>
              </CircleMarker>
            );
          })}
      </MapContainer>

      {/* Layer controls */}
      <div className="absolute right-3 top-3 z-[500] rounded-xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur">
        <p className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-navy-950">
          <Layers className="h-3.5 w-3.5" /> Layers
        </p>
        <div className="space-y-1.5">
          {LAYER_META.map((l) => (
            <label key={l.key} className="flex cursor-pointer items-center gap-2 text-xs text-slate-700">
              <input
                type="checkbox"
                checked={layers[l.key]}
                onChange={() => setLayers((prev) => ({ ...prev, [l.key]: !prev[l.key] }))}
                className={cn("h-3.5 w-3.5 rounded accent-navy-700")}
              />
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: l.color }} />
              {l.label}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
