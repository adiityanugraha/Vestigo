"use client";

// Market Narrator (Phase 5 Day 15) — ringkasan kondisi pasar harian.
// GET /api/market-summary (auto-load).

import { getMarketSummary } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton, CachedBadge } from "../CardStatus";

export function MarketNarrator() {
  const state = useApi(getMarketSummary, []);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-base font-semibold text-white">Market Narrator</h2>
        {state.status === "ready" && <CachedBadge cached={state.data.cached} />}
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Ringkasan pasar: breadth, rotasi sektor, dan strategi terbaik.
      </p>

      {state.status === "loading" && <CardSkeleton />}
      {state.status === "error" && <CardError message={state.error} onRetry={state.reload} />}
      {state.status === "ready" && (
        <div className="space-y-3 text-sm">
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-slate-400">
            {state.data.bullish_ratio != null && (
              <span>
                Bullish Ratio:{" "}
                <span className="font-semibold text-white">
                  {(state.data.bullish_ratio * 100).toFixed(0)}%
                </span>
              </span>
            )}
            <span>
              Naik/Turun:{" "}
              <span className="font-semibold text-emerald-300">{state.data.advancers ?? "-"}</span>
              {" / "}
              <span className="font-semibold text-rose-300">{state.data.decliners ?? "-"}</span>
            </span>
            {state.data.best_strategy && (
              <span>
                Strategi terbaik:{" "}
                <span className="font-semibold text-sky-200">{state.data.best_strategy}</span>
              </span>
            )}
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-400">
            <span>Sektor leading: {state.data.leading_sectors.join(", ") || "-"}</span>
            <span>Sektor lagging: {state.data.lagging_sectors.join(", ") || "-"}</span>
          </div>

          {state.data.summary && <p className="text-slate-200">{state.data.summary}</p>}
          <p className="text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
