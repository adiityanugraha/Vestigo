"use client";

import { useCallback, useState } from "react";

// Untuk aksi async yang dipicu user (tombol), beda dari useApi yang auto-fetch
// saat mount. Menstandarkan state idle|loading|ready|error untuk komponen AI
// on-demand (AI Analyst, Explain Score, Comparator, Portfolio Advisor/Builder).

export type AsyncState<T> =
  | { status: "idle"; data: null; error: null }
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useAsyncAction<T>() {
  const [state, setState] = useState<AsyncState<T>>({
    status: "idle",
    data: null,
    error: null,
  });

  const run = useCallback(async (action: () => Promise<T>) => {
    setState({ status: "loading", data: null, error: null });
    try {
      const data = await action();
      setState({ status: "ready", data, error: null });
    } catch (err) {
      setState({
        status: "error",
        data: null,
        error: err instanceof Error ? err.message : "Gagal memuat",
      });
    }
  }, []);

  return { ...state, run };
}
