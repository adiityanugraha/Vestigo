"use client";

// Monte Carlo (Phase 4 Day 15).
// Pemilih strategi -> sebaran hasil 1 tahun (histogram) + persentil dari
// GET /api/monte-carlo/{strategy}.

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getMonteCarlo } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "../CardStatus";

const STRATEGIES = [
  { key: "bsjp", label: "BSJP" },
  { key: "bpjs", label: "BPJS" },
  { key: "breakout", label: "Breakout" },
  { key: "trend_following", label: "Trend Following" },
  { key: "potential_reversal", label: "Potential Reversal" },
];

function pct(value: number): string {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

function Stat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`text-sm font-semibold ${tone}`}>{value}</p>
    </div>
  );
}

export function MonteCarloChart() {
  const [strategy, setStrategy] = useState("bpjs");
  const { status, data, error, reload } = useApi(() => getMonteCarlo(strategy), [strategy]);

  const chartData =
    data?.histogram.map((b) => ({
      mid: ((b.start + b.end) / 2) * 100,
      count: b.count,
      positive: (b.start + b.end) / 2 >= 0,
    })) ?? [];

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Monte Carlo</h2>
        {data && <CachedBadge cached={data.cached} />}
      </div>
      <p className="mb-3 text-xs text-slate-500">
        Sebaran kemungkinan hasil 1 tahun (bootstrap return historis).
      </p>

      <div className="mb-4 flex flex-wrap gap-2">
        {STRATEGIES.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setStrategy(s.key)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              strategy === s.key
                ? "border-sky-400/40 bg-sky-500/15 text-sky-200"
                : "border-white/10 text-slate-400 hover:bg-white/5"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Stat
              label="Prob. Profit"
              value={`${(data.probability_of_profit * 100).toFixed(0)}%`}
              tone="text-emerald-300"
            />
            <Stat label="Worst (P5)" value={pct(data.percentiles.p5)} tone="text-rose-300" />
            <Stat label="Median" value={pct(data.percentiles.p50)} tone="text-slate-100" />
            <Stat label="Best (P95)" value={pct(data.percentiles.p95)} tone="text-emerald-300" />
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer height="100%" width="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -16 }}>
                <CartesianGrid stroke="#ffffff14" vertical={false} />
                <XAxis
                  dataKey="mid"
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} width={36} />
                <Tooltip
                  contentStyle={{
                    background: "#0b1120",
                    border: "1px solid #ffffff1a",
                    borderRadius: 8,
                    color: "#e2e8f0",
                    fontSize: 12,
                  }}
                  formatter={(value) => [`${value} lintasan`, "Frekuensi"]}
                  labelFormatter={(label) => `Return ~${Number(label).toFixed(1)}%`}
                />
                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.positive ? "#34d399" : "#f43f5e"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data.disclaimer}</p>
        </>
      )}
    </section>
  );
}
