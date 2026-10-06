"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./types";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Minimal data-fetching hook: loading / error / empty states for every
 * dashboard section, wired to a real backend endpoint.
 */
export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const refetch = useCallback(() => {
    // Event handler (not an effect): safe to set state here.
    setLoading(true);
    setNonce((n) => n + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetcher()
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : "Could not reach the server.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps]);

  return { data, loading, error, refetch };
}
