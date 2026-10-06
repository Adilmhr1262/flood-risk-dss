"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TriangleAlert } from "lucide-react";
import { useApi } from "@/lib/api/hooks";
import { gisApi } from "@/lib/api/endpoints";
import { formatProbability } from "@/lib/format";
import type { GeoJSONFeatureCollection } from "@/lib/api/types";

/**
 * District risk map rendered with Leaflet from the live
 * GET /gis/risk-layer GeoJSON endpoint.
 *
 * Loaded client-side only (Leaflet needs `window`); shows skeleton and
 * error states while the layer loads.
 */

const LeafletMap = dynamic(() => import("./LeafletMapInner"), {
  ssr: false,
  loading: () => <Skeleton className="h-full w-full rounded-xl" />,
});

function riskColor(level: unknown): string {
  const l = String(level ?? "").toUpperCase();
  if (l === "HIGH") return "#dc2626";
  if (l === "MEDIUM") return "#f59e0b";
  return "#10b981";
}

function popupHtml(props: Record<string, unknown>): string {
  const name = String(props.district_name ?? props.name ?? "District");
  const level = String(props.risk_level ?? "—");
  const prob = formatProbability(
    typeof props.probability === "number" ? props.probability : null,
  );
  const vuln =
    typeof props.vulnerability_index === "number"
      ? props.vulnerability_index.toFixed(3)
      : "—";
  return (
    `<div style="font-family:inherit;min-width:180px">` +
    `<strong style="font-size:14px">${name}</strong><br/>` +
    `<span>Risk level: <strong>${level}</strong></span><br/>` +
    `<span>Probability: ${prob}</span><br/>` +
    `<span>Vulnerability index: ${vuln}</span>` +
    `</div>`
  );
}

export function MapComponent({ className }: { className?: string }) {
  const { data, loading, error, refetch } = useApi<GeoJSONFeatureCollection>(
    () => gisApi.riskLayer(),
  );
  const [failed, setFailed] = useState(false);

  // Reset the map-error flag whenever fresh data arrives.
  // (Render-time adjustment — the documented alternative to setState in an effect.)
  const [lastData, setLastData] = useState(data);
  if (lastData !== data) {
    setLastData(data);
    setFailed(false);
  }

  const geoJson = useMemo(() => data, [data]);

  return (
    <div className={className}>
      {loading && <Skeleton className="h-full min-h-[420px] w-full rounded-xl" />}
      {!loading && error && (
        <Alert variant="destructive" className="min-h-[420px]">
          <TriangleAlert />
          <AlertDescription>
            The risk map could not be loaded: {error}{" "}
            <button
              onClick={refetch}
              className="ml-1 font-semibold underline underline-offset-2"
            >
              Retry
            </button>
          </AlertDescription>
        </Alert>
      )}
      {!loading && !error && geoJson && !failed && (
        <div className="h-full min-h-[420px] w-full overflow-hidden rounded-xl border border-slate-200">
          <LeafletMap
            geoJson={geoJson}
            onError={() => setFailed(true)}
            styleFor={(f) => ({
              color: "#0a1a33",
              weight: 1,
              fillColor: riskColor(f.properties?.risk_level),
              fillOpacity: 0.55,
            })}
            pointColorFor={(f) =>
              typeof f.properties?.color === "string"
                ? String(f.properties.color)
                : riskColor(f.properties?.risk_level)
            }
            popupFor={(f) => popupHtml(f.properties ?? {})}
          />
        </div>
      )}
      {failed && (
        <Alert variant="warning">
          <TriangleAlert />
          <AlertDescription>
            The map library failed to initialise in this browser. District risk
            data is still available in the tables below.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
