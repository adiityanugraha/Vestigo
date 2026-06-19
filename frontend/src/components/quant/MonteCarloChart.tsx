"use client";

// Monte Carlo (Phase 4). Pemilih strategi -> sebaran hasil 1 tahun + persentil.
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
import { fmtPctFromFraction, fmtScore } from "@/lib/format";
import { VCard } from "../vestigo/Card";
import { CardError, CardSkeleton } from "../CardStatus";

const STRATEGIES = [
  { key: "bsjp", label: "BSJP" },
  { key: "bpjs", label: "BPJS" },
  { key: "breakout", label: "Breakout" },
  { key: "trend_following", label: "Trend Following" },
  { key: "potential_reversal", label: "Potential Reversal" },
];

const TOOLTIP_STYLE = {
  background: "var(--s1)",
  border: "1px solid var(--bd2)",
  borderRadius: 8,
  color: "var(--t1)",
  fontSize: 12,
} as const;

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
    <VCard
      title="Monte Carlo"
      sub="Sebaran kemungkinan hasil 1 tahun (bootstrap return historis)"
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
          <div className="tile-grid-4">
            <div className="tile">
              <p className="tile-label">Prob. profit</p>
              <p className="tile-val mono num-up">
                {fmtScore(data.probability_of_profit * 100, 0)}%
              </p>
            </div>
            <div className="tile">
              <p className="tile-label">Worst (P5)</p>
              <p className="tile-val mono num-down">{fmtPctFromFraction(data.percentiles.p5, 1)}</p>
            </div>
            <div className="tile">
              <p className="tile-label">Median</p>
              <p className="tile-val mono">{fmtPctFromFraction(data.percentiles.p50, 1)}</p>
            </div>
            <div className="tile">
              <p className="tile-label">Best (P95)</p>
              <p className="tile-val mono num-up">{fmtPctFromFraction(data.percentiles.p95, 1)}</p>
            </div>
          </div>

          <div style={{ height: 224, width: "100%" }}>
            <ResponsiveContainer height="100%" width="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -16 }}>
                <CartesianGrid stroke="#ffffff14" vertical={false} />
                <XAxis
                  dataKey="mid"
                  stroke="#6b6157"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                />
                <YAxis stroke="#6b6157" tick={{ fontSize: 10 }} tickLine={false} width={36} />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(value) => [`${value} lintasan`, "Frekuensi"]}
                  labelFormatter={(label) => `Return ~${Number(label).toFixed(1)}%`}
                />
                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.positive ? "#22c55e" : "#ef4444"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="feature-note">
            Ribuan simulasi acak memperkirakan sebaran kemungkinan hasil 1 tahun strategi ini.
          </p>
          <p className="disclaimer">{data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
