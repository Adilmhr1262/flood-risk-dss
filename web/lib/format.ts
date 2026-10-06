/**
 * Probability formatting helpers.
 *
 * Backend endpoints return flood probability on different scales:
 * - GET /public/risk-check and /risk/* return a 0–1 fraction (e.g. 0.82)
 * - GET /gis/risk-layer and /public/map/risk-zones return a 0–100
 *   percentage (e.g. 82.0)
 *
 * These helpers normalise either scale to a whole-number percent so the
 * UI never shows values like "8200%".
 */

/** Convert a probability value on either scale to a 0–100 number. */
export function probabilityPct(p: number | null | undefined): number | null {
  if (p === null || p === undefined || Number.isNaN(p)) return null;
  const v = p <= 1 ? p * 100 : p;
  return Math.max(0, Math.min(100, Math.round(v)));
}

/** Format a probability value as "82%" (either input scale accepted). */
export function formatProbability(
  p: number | null | undefined,
  fallback = "—",
): string {
  const pct = probabilityPct(p);
  return pct === null ? fallback : `${pct}%`;
}

/** Relative "x minutes ago" label for ISO timestamps. */
export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const mins = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}
