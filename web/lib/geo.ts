"use client";

import { useCallback, useState } from "react";

export interface LatLng {
  lat: number;
  lng: number;
}

/** Great-circle distance in kilometres between two WGS84 points. */
export function haversineKm(
  aLat: number,
  aLng: number,
  bLat: number,
  bLng: number,
): number {
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

interface GeoState {
  loc: LatLng | null;
  locating: boolean;
  error: string | null;
  request: () => void;
}

/**
 * Opt-in browser geolocation. The coordinates never leave the device —
 * callers use them only for client-side distance sorting.
 */
export function useGeolocation(): GeoState {
  const [loc, setLoc] = useState<LatLng | null>(null);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setError("Location is not available on this device.");
      return;
    }
    setLocating(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLoc({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setError("Could not get your location. Check the browser permission.");
        setLocating(false);
      },
      { timeout: 10000 },
    );
  }, []);

  return { loc, locating, error, request };
}

/** Nearest item from a list of {lat, lng} points to the user's location. */
export function nearestTo<T extends { lat: number; lng: number }>(
  loc: LatLng,
  points: T[],
): (T & { distanceKm: number }) | null {
  let best: (T & { distanceKm: number }) | null = null;
  for (const p of points) {
    if (!Number.isFinite(p.lat) || !Number.isFinite(p.lng)) continue;
    const d = haversineKm(loc.lat, loc.lng, p.lat, p.lng);
    if (!best || d < best.distanceKm) best = { ...p, distanceKm: d };
  }
  return best;
}
