"use client";

// Strategy Benchmark (Phase 4 Day 14).
// Tabel metrik seluruh strategi tervalidasi + baris pembanding IHSG dari
// GET /api/benchmark. Menandai strategi yang mengalahkan pasar.

import { getBenchmark, type BenchmarkRow } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "../CardStatus";

function pct(value: number): string {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

function toneFor(value: number): string {
  if (value > 0) return "text-emerald-300";
  if (value < 0) return "text-rose-300";
  return "text-slate-300";
}

function Row({ row, market }: { row: BenchmarkRow; market: boolean }) {
  const m = row.metrics;
  const beats = row.beats_market_cagr;
  return (
    <tr
      className={
        market
          ? "border-t border-white/15 bg-white/[0.04] font-medium"
          : "border-t border-white/5"
      }
    >
      <td className="py-2 pr-3 text-left">
        <div className="flex items-center gap-2">
          <span className="text-white">{row.name ?? row.strategy}</span>
          {!market && beats === true && (
            <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300">
              &gt; pasar
            </span>
          )}
        </div>
      </td>
      <td className={`py-2 px-3 text-right tabular-nums ${toneFor(m.cagr)}`}>{pct(m.cagr)}</td>
      <td className="py-2 px-3 text-right tabular-nums text-slate-200">
        {(m.winrate * 100).toFixed(0)}%
      </td>
      <td className="py-2 px-3 text-right tabular-nums text-slate-200">
        {m.sharpe_ratio.toFixed(2)}
      </td>
      <td className="py-2 px-3 text-right tabular-nums text-rose-300/90">
        {pct(m.max_drawdown)}
      </td>
      <td className="py-2 pl-3 text-right tabular-nums text-slate-200">
        {m.profit_factor.toFixed(2)}
      </td>
    </tr>
  );
}

export function StrategyBenchmark() {
  const { status, data, error, reload } = useApi(() => getBenchmark(), []);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Strategy Benchmark</h2>
        {data && <CachedBadge cached={data.cached} />}
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Performa 5 strategi teknikal vs IHSG (buy &amp; hold) — apakah mengalahkan pasar?
      </p>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3 text-left font-medium">Strategi</th>
                  <th className="py-2 px-3 text-right font-medium">CAGR</th>
                  <th className="py-2 px-3 text-right font-medium">Winrate</th>
                  <th className="py-2 px-3 text-right font-medium">Sharpe</th>
                  <th className="py-2 px-3 text-right font-medium">Max DD</th>
                  <th className="py-2 pl-3 text-right font-medium">PF</th>
                </tr>
              </thead>
              <tbody>
                {data.strategies.map((row) => (
                  <Row key={row.strategy} row={row} market={false} />
                ))}
                <Row row={data.market} market />
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data.disclaimer}</p>
        </>
      )}
    </section>
  );
}
