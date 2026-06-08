"use client";

import { getMarketBreadth, type Mover } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function signed(value: number): string {
  const pct = (value * 100).toFixed(2);
  return value > 0 ? `+${pct}%` : `${pct}%`;
}

function sectorTone(avg: number): string {
  if (avg >= 0.015) return "bg-emerald-500/80 text-slate-950";
  if (avg > 0) return "bg-emerald-500/35 text-emerald-50";
  if (avg === 0) return "bg-slate-500/30 text-slate-100";
  if (avg > -0.015) return "bg-rose-500/35 text-rose-50";
  return "bg-rose-500/80 text-slate-950";
}

function MoverList({ title, movers, tone }: { title: string; movers: Mover[]; tone: string }) {
  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</p>
      <ul className="space-y-1.5">
        {movers.map((m) => (
          <li key={m.ticker} className="flex items-center justify-between text-sm">
            <span className="font-medium text-slate-200">{m.ticker}</span>
            <span className={`tabular-nums font-semibold ${tone}`}>{signed(m.change_pct)}</span>
          </li>
        ))}
        {movers.length === 0 && <li className="text-sm text-slate-500">—</li>}
      </ul>
    </div>
  );
}

export function MarketBreadthCard() {
  const { status, data, error, reload } = useApi(() => getMarketBreadth(), []);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Market Breadth</h2>
        <div className="flex items-center gap-2">
          {data && <CachedBadge cached={data.cached} />}
          <span className="text-xs font-medium text-slate-400">{data?.date ?? "IDX"}</span>
        </div>
      </div>
      <p className="mb-4 text-xs text-slate-500">Kesehatan pasar keseluruhan</p>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-lg border border-emerald-400/20 bg-emerald-500/10 p-3">
              <p className="text-xs text-emerald-300">Naik</p>
              <p className="mt-1 text-xl font-bold tabular-nums text-emerald-100">
                {data.advancers}
              </p>
            </div>
            <div className="rounded-lg border border-rose-400/20 bg-rose-500/10 p-3">
              <p className="text-xs text-rose-300">Turun</p>
              <p className="mt-1 text-xl font-bold tabular-nums text-rose-100">{data.decliners}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/[0.04] p-3">
              <p className="text-xs text-slate-400">Bullish Ratio</p>
              <p className="mt-1 text-xl font-bold tabular-nums text-white">
                {data.bullish_ratio === null ? "—" : `${(data.bullish_ratio * 100).toFixed(0)}%`}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <MoverList title="Top Gainers" movers={data.top_gainers} tone="text-emerald-300" />
            <MoverList title="Top Losers" movers={data.top_losers} tone="text-rose-300" />
          </div>

          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Performa Sektor
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {data.sector_performance.map((s) => (
                <div
                  key={s.sector}
                  className={`rounded-lg p-2.5 ${sectorTone(s.avg_change_pct)}`}
                  title={`${s.count} saham`}
                >
                  <p className="truncate text-[11px] font-semibold">{s.sector}</p>
                  <p className="text-sm font-bold tabular-nums">{signed(s.avg_change_pct)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
