"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import type { GeoJSONFeatureCollection, GeoJSONFeature } from "@/lib/api/types";
import L from "leaflet";

interface LeafletMapInnerProps {
  geoJson: GeoJSONFeatureCollection;
  onError: () => void;
  styleFor: (feature: GeoJSONFeature) => L.PathOptions;
  popupFor: (feature: GeoJSONFeature) => string;
  pointColorFor?: (feature: GeoJSONFeature) => string;
}

function FitBounds({ geoJson }: { geoJson: GeoJSONFeatureCollection }) {
  const map = useMap();
  useEffect(() => {
    try {
      const layer = L.geoJSON(geoJson as unknown as GeoJSON.GeoJsonObject);
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.15));
    } catch {
      /* keep default view */
    }
  }, [geoJson, map]);
  return null;
}

/**
 * Inner Leaflet map. Imported dynamically with ssr:false from MapComponent.
 * Centred on Sindh, Pakistan; base tiles from OpenStreetMap.
 */
export default function LeafletMapInner({
  geoJson,
  onError,
  styleFor,
  popupFor,
  pointColorFor,
}: LeafletMapInnerProps) {
  useEffect(() => {
    // Fix default marker icon paths under Next.js bundling.
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });
    } catch {
      onError();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <MapContainer
      center={[26.5, 68.5]}
      zoom={7}
      scrollWheelZoom
      className="h-full min-h-[420px] w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON
        key={JSON.stringify(geoJson).length}
        data={geoJson as unknown as GeoJSON.GeoJsonObject}
        style={(f) => styleFor(f as unknown as GeoJSONFeature)}
        pointToLayer={(feature, latlng) => {
          const f = feature as unknown as GeoJSONFeature;
          return L.circleMarker(latlng, {
            radius: 10,
            color: "#0a1a33",
            weight: 1.5,
            fillColor: pointColorFor
              ? pointColorFor(f)
              : styleFor(f).fillColor,
            fillOpacity: 0.85,
          });
        }}
        onEachFeature={(feature, layer) => {
          layer.bindPopup(popupFor(feature as unknown as GeoJSONFeature));
        }}
      />
      <FitBounds geoJson={geoJson} />
    </MapContainer>
  );
}
