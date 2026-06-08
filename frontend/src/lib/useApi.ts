"use client";

import { useCallback, useEffect, useState } from "react";

// Hook fetch generik: standarisasi loading / ready / error + retry untuk
// seluruh card yang mengambil dari REST API backend (Day 14).

export type ApiState<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
): ApiState<T> & { reload: () => void } {
  const [state, setState] = useState<ApiState<T>>({
    status: "loading",
    data: null,
    error: null,
  });
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let ignore = false;
    setState({ status: "loading", data: null, error: null });

    fetcher()
      .then((data) => {
        if (!ignore) setState({ status: "ready", data, error: null });
      })
      .catch((error: unknown) => {
        if (!ignore) {
          setState({
            status: "error",
            data: null,
            error: error instanceof Error ? error.message : "Permintaan gagal",
          });
        }
      });

    return () => {
      ignore = true;
    };
    // fetcher sengaja tidak di-deps (identitasnya berubah tiap render);
    // dikontrol lewat `deps` + `nonce` (retry).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { ...state, reload };
}
