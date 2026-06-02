"use client";

import { useEffect, useState } from "react";
import { fetchManyDailyOhlcv } from "@/lib/fetchData";
import type { OhlcvBar } from "@/lib/indicators";

const WATCHLIST = ["BBCA", "TLKM", "ASII"];

type MarketDataState =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: Record<string, OhlcvBar[]>; error: null }
  | { status: "error"; data: null; error: string };

export function MarketDataStatus() {
  const [state, setState] = useState<MarketDataState>({
    status: "loading",
    data: null,
    error: null,
  });

  useEffect(() => {
    let ignore = false;

    fetchManyDailyOhlcv(WATCHLIST)
      .then((data) => {
        if (!ignore) {
          setState({ status: "ready", data, error: null });
        }
      })
      .catch((error: unknown) => {
        if (!ignore) {
          const message =
            error instanceof Error ? error.message : "Failed to fetch market data";

          setState({ status: "error", data: null, error: message });
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-4 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-base font-semibold text-white">Market Data</h2>
          <p className="mt-1 text-sm text-slate-400">
            Yahoo Finance daily OHLCV with local cache
          </p>
        </div>
        <span className="rounded-md border border-white/10 px-3 py-1 text-xs font-medium text-slate-300">
          {state.status}
        </span>
      </div>

      {state.status === "loading" && (
        <p className="text-sm text-slate-400">Fetching IDX watchlist...</p>
      )}

      {state.status === "error" && (
        <p className="text-sm text-rose-300">{state.error}</p>
      )}

      {state.status === "ready" && (
        <div className="grid gap-3 md:grid-cols-3">
          {Object.entries(state.data).map(([symbol, bars]) => {
            const latest = bars.at(-1);

            return (
              <div
                className="rounded-lg border border-white/10 bg-slate-950/60 p-4"
                key={symbol}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-white">{symbol}</p>
                  <p className="text-xs text-slate-400">{bars.length} bars</p>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-slate-500">Latest</p>
                    <p className="mt-1 text-slate-200">{latest?.date ?? "-"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">Close</p>
                    <p className="mt-1 text-emerald-300">
                      {latest?.close.toLocaleString("id-ID") ?? "-"}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
