"use client";

// Equity Curve (Phase 4 Day 14).
// Pemilih strategi -> kurva pertumbuhan modal + drawdown dari
// GET /api/equity-curve/{strategy} (Recharts).

import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getEquityCurve } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "../CardStatus";

const STRATEGIES = [
  { key: "bsjp", label: "BSJP" },
  { key: "bpjs", label: "BPJS" },
  { key: "breakout", label: "Breakout" },
  { key: "trend_following", label: "Trend Following" },
  { key: "potential_reversal", label: "Potential Reversal" },
];

const INITIAL_CAPITAL = 100_000_000;

function rpJuta(value: number): string {
  return `${(value / 1e6).toFixed(0)} jt`;
}

function pct(value: number): string {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

export function EquityCurveChart() {
  const [strategy, setStrategy] = useState("bpjs");
  const { status, data, error, reload } = useApi(
    () => getEquityCurve(strategy, INITIAL_CAPITAL),
    [strategy],
  );

  const chartData =
    data?.points.map((p) => ({
      date: p.date,
      value: p.value,
      drawdown: p.drawdown * 100,
    })) ?? [];

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Equity Curve</h2>
        {data && <CachedBadge cached={data.cached} />}
      </div>
      <p className="mb-3 text-xs text-slate-500">
        Pertumbuhan modal Rp 100 jt + drawdown (rebalancing kohort 30 hari).
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
          <div className="mb-3 flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span className="text-slate-400">
              Nilai akhir:{" "}
              <span className="font-semibold text-white">
                Rp {data.summary.final_value.toLocaleString("id-ID")}
              </span>
            </span>
            <span className="text-slate-400">
              Total return:{" "}
              <span
                className={`font-semibold ${
                  data.summary.total_return >= 0 ? "text-emerald-300" : "text-rose-300"
                }`}
              >
                {pct(data.summary.total_return)}
              </span>
            </span>
            <span className="text-slate-400">
              Max DD:{" "}
              <span className="font-semibold text-rose-300">{pct(data.summary.max_drawdown)}</span>
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer height="100%" width="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -8 }}>
                <defs>
                  <linearGradient id="fillEquity" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="fillDd" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity={0} />
                    <stop offset="100%" stopColor="#f43f5e" stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#ffffff14" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  minTickGap={48}
                  tickFormatter={(d: string) => d.slice(0, 7)}
                />
                <YAxis
                  yAxisId="equity"
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  width={52}
                  tickFormatter={rpJuta}
                />
                <YAxis
                  yAxisId="dd"
                  orientation="right"
                  stroke="#64748b"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  width={40}
                  tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                />
                <Tooltip
                  contentStyle={{
                    background: "#0b1120",
                    border: "1px solid #ffffff1a",
                    borderRadius: 8,
                    color: "#e2e8f0",
                    fontSize: 12,
                  }}
                  formatter={(value, name) =>
                    name === "Drawdown"
                      ? `${Number(value).toFixed(1)}%`
                      : `Rp ${Number(value).toLocaleString("id-ID")}`
                  }
                />
                <Area
                  yAxisId="dd"
                  dataKey="drawdown"
                  name="Drawdown"
                  fill="url(#fillDd)"
                  stroke="#f43f5e"
                  strokeWidth={1}
                  type="monotone"
                />
                <Area
                  yAxisId="equity"
                  dataKey="value"
                  name="Equity"
                  fill="url(#fillEquity)"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  type="monotone"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data.disclaimer}</p>
        </>
      )}
    </section>
  );
}
