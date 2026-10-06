"use client";

import { ApiError } from "./types";

/**
 * Low-level HTTP client for the Flood Risk DSS FastAPI backend.
 *
 * - Base URL from NEXT_PUBLIC_API_BASE_URL (falls back to localhost).
 * - Attaches the JWT access token from localStorage.
 * - On 401, attempts one refresh-token rotation before failing.
 *
 * Token storage keys are shared with the AuthProvider (lib/auth).
 */
export const ACCESS_TOKEN_KEY = "floodsafe.access_token";
export const REFRESH_TOKEN_KEY = "floodsafe.refresh_token";

declare global {
  interface Window {
    /** Runtime API base URL injected by the server layout (see app/layout.tsx).
     * Lets the deployment target a new backend without a rebuild. */
    __API_BASE_URL__?: string;
  }
}

export function apiBase(): string {
  const base =
    (typeof window !== "undefined" && window.__API_BASE_URL__) ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000/api/v1";
  return base.replace(/\/$/, "");
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, access);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  /** Set false for /auth/login and /auth/register. */
  auth?: boolean;
  query?: Record<string, string | number | boolean | undefined | null>;
}

async function rawRequest<T>(
  path: string,
  opts: RequestOptions,
  token: string | null,
): Promise<T> {
  const url = new URL(apiBase() + path);
  if (opts.query) {
    for (const [k, v] of Object.entries(opts.query)) {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    }
  }
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url.toString(), {
    method: opts.method ?? "GET",
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  if (res.status === 204) return undefined as T;

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON body */
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : `HTTP ${res.status}`;
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const data = await rawRequest<{
      access_token: string;
      refresh_token: string;
    }>("/auth/refresh", { method: "POST", body: { refresh_token: refresh }, auth: false }, null);
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

/** Authenticated JSON request against the backend API. */
export async function apiRequest<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const needsAuth = opts.auth !== false;
  try {
    return await rawRequest<T>(path, opts, needsAuth ? getAccessToken() : null);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401 && needsAuth) {
      const fresh = await refreshAccessToken();
      if (fresh) return rawRequest<T>(path, opts, fresh);
      // Broadcast so the AuthProvider can sign the user out.
      window.dispatchEvent(new CustomEvent("floodsafe:unauthorized"));
    }
    throw err;
  }
}
