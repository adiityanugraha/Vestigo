"use client";

// Market Replay (Phase 4 Day 14).
// Pemilih tanggal historis -> kandidat per strategi pada tanggal itu + performa
// forward (+1/+3/+7/+30 hari) dari GET /api/replay/{date}.

import { useState } from "react";
import { getReplay, type ReplayCandidate } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "../CardStatus";

const STRATEGY_LABELS: Record<string, string> = {
  bsjp: "BSJP",
  bpjs: "BPJS",
  breakout: "Breakout",
  trend_following: "Trend Following",
  potential_reversal: "Potential Reversal",
};

const DEFAULT_DATE = "2024-01-15";

function Ret({ value }: { value: number | null }) {
  if (value === null) return <span className="text-slate-600">n/a</span>;
  const tone = value > 0 ? "text-emerald-300" : value < 0 ? "text-rose-300" : "text-slate-300";
  return (
    <span className={`tabular-nums ${tone}`}>
      {value >= 0 ? "+" : ""}
      {(value * 100).toFixed(1)}%
    </span>
  );
}

function StrategyBucket({ label, items }: { label: string; items: ReplayCandidate[] }) {
  if (items.length === 0) return null;
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
      <h3 className="mb-2 text-sm font-semibold text-sky-200">{label}</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-slate-500">
              <th className="py-1 pr-2 text-left font-medium">Saham</th>
              <th className="py-1 px-2 text-right font-medium">Harga</th>
              <th className="py-1 px-2 text-right font-medium">+1h</th>
              <th className="py-1 px-2 text-right font-medium">+7h</th>
              <th className="py-1 pl-2 text-right font-medium">+30h</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.ticker} className="border-t border-white/5">
                <td className="py-1 pr-2 text-left">
                  <span className="font-medium text-white">{c.ticker}</span>
                </td>
                <td className="py-1 px-2 text-right tabular-nums text-slate-300">
                  {c.price?.toLocaleString("id-ID") ?? "-"}
                </td>
                <td className="py-1 px-2 text-right">
                  <Ret value={c.ret["1d"]} />
                </td>
                <td className="py-1 px-2 text-right">
                  <Ret value={c.ret["7d"]} />
                </td>
                <td className="py-1 pl-2 text-right">
                  <Ret value={c.ret["30d"]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function MarketReplay() {
  const [date, setDate] = useState(DEFAULT_DATE);
  const { status, data, error, reload } = useApi(() => getReplay(date), [date]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Market Replay</h2>
        {data && <CachedBadge cached={data.cached} />}
      </div>
      <p className="mb-3 text-xs text-slate-500">
        Putar ulang kandidat screening pada tanggal historis + performa setelahnya.
      </p>

      <div className="mb-4 flex items-center gap-3">
        <input
          type="date"
          value={date}
          min={data?.data_range.earliest ?? undefined}
          max={data?.data_range.latest ?? undefined}
          onChange={(e) => e.target.value && setDate(e.target.value)}
          className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-sm text-white [color-scheme:dark]"
        />
        {data && (
          <span className="text-xs text-slate-500">
            {data.total_candidates} kandidat
          </span>
        )}
      </div>

      {status === "loading" && <CardSkeleton lines={5} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <>
          {data.total_candidates === 0 ? (
            <p className="rounded-lg border border-white/5 bg-white/[0.02] p-4 text-sm text-slate-400">
              Tidak ada kandidat lolos pada tanggal ini. Coba tanggal lain dalam rentang{" "}
              {data.data_range.earliest} – {data.data_range.latest}.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {Object.entries(data.strategies).map(([key, items]) => (
                <StrategyBucket
                  key={key}
                  label={STRATEGY_LABELS[key] ?? key}
                  items={items}
                />
              ))}
            </div>
          )}
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data.disclaimer}</p>
        </>
      )}
    </section>
  );
}
