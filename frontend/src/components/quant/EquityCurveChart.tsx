"use client";

// Equity Curve (Phase 4). Pemilih strategi -> kurva pertumbuhan modal + drawdown.
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
import { fmtPctFromFraction, fmtValue } from "@/lib/format";
import { VCard } from "../vestigo/Card";
import { CardError, CardSkeleton } from "../CardStatus";

const STRATEGIES = [
  { key: "bsjp", label: "BSJP" },
  { key: "bpjs", label: "BPJS" },
  { key: "breakout", label: "Breakout" },
  { key: "trend_following", label: "Trend Following" },
  { key: "potential_reversal", label: "Potential Reversal" },
];

const INITIAL_CAPITAL = 100_000_000;
const TOOLTIP_STYLE = {
  background: "var(--s1)",
  border: "1px solid var(--bd2)",
  borderRadius: 8,
  color: "var(--t1)",
  fontSize: 12,
} as const;

function rpJuta(value: number): string {
  return `${(value / 1e6).toFixed(0)} jt`;
}

export function EquityCurveChart() {
  const [strategy, setStrategy] = useState("bpjs");
  const { status, data, error, reload } = useApi(
    () => getEquityCurve(strategy, INITIAL_CAPITAL),
    [strategy],
  );

  const chartData =
    data?.points.map((p) => ({ date: p.date, value: p.value, drawdown: p.drawdown * 100 })) ?? [];

  return (
    <VCard
      title="Equity Curve"
      sub="Pertumbuhan modal Rp 100 jt + drawdown (rebalancing 30 hari)"
      subMono={false}
      cached={!!data?.cached}
    >
      <div className="cmp-row">
        {STRATEGIES.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setStrategy(s.key)}
            className={`pill-chip ${strategy === s.key ? "pill-on" : ""}`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <>
          <div className="tile-grid-3">
            <div className="tile">
              <p className="tile-label">Nilai akhir</p>
              <p className="tile-val mono">{fmtValue(data.summary.final_value)}</p>
            </div>
            <div className="tile">
              <p className="tile-label">Total return</p>
              <p
                className={`tile-val mono ${data.summary.total_return >= 0 ? "num-up" : "num-down"}`}
              >
                {fmtPctFromFraction(data.summary.total_return, 1)}
              </p>
            </div>
            <div className="tile">
              <p className="tile-label">Max DD</p>
              <p className="tile-val mono num-down">
                {fmtPctFromFraction(data.summary.max_drawdown, 1)}
              </p>
            </div>
          </div>

          <div style={{ height: 288, width: "100%" }}>
            <ResponsiveContainer height="100%" width="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -8 }}>
                <defs>
                  <linearGradient id="fillEquity" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#c19a6b" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#c19a6b" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="fillDd" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity={0} />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#ffffff14" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#6b6157"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  minTickGap={48}
                  tickFormatter={(d: string) => d.slice(0, 7)}
                />
                <YAxis
                  yAxisId="equity"
                  stroke="#6b6157"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  width={52}
                  tickFormatter={rpJuta}
                />
                <YAxis
                  yAxisId="dd"
                  orientation="right"
                  stroke="#6b6157"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  width={40}
                  tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
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
                  stroke="#ef4444"
                  strokeWidth={1}
                  type="monotone"
                />
                <Area
                  yAxisId="equity"
                  dataKey="value"
                  name="Equity"
                  fill="url(#fillEquity)"
                  stroke="#c19a6b"
                  strokeWidth={2}
                  type="monotone"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="feature-note">
            Simulasi pertumbuhan modal Rp 100 jt bila mengikuti strategi ini, beserta drawdown-nya.
          </p>
          <p className="disclaimer">{data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
