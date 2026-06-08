"use client";

import { getRisk } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function riskTone(risk: string): string {
  if (risk === "LOW") return "text-emerald-300 border-emerald-400/30 bg-emerald-500/10";
  if (risk === "HIGH") return "text-rose-300 border-rose-400/30 bg-rose-500/10";
  return "text-amber-300 border-amber-400/30 bg-amber-500/10";
}

function barColor(risk: string): string {
  if (risk === "LOW") return "bg-emerald-400";
  if (risk === "HIGH") return "bg-rose-400";
  return "bg-amber-400";
}

function pct(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function RiskMeterCard({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getRisk(symbol), [symbol]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white">Risk Meter</h2>
          <p className="mt-1 text-xs text-slate-500">{symbol}</p>
        </div>
        {data && <CachedBadge cached={data.cached} />}
      </div>

      {status === "loading" && <CardSkeleton lines={4} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3">
            <span
              className={`rounded-md border px-2.5 py-1 text-sm font-semibold ${riskTone(data.risk)}`}
            >
              {data.risk} RISK
            </span>
            <div className="text-right">
              <p className="text-xs text-slate-500">Risk Score</p>
              <p className="text-2xl font-bold tabular-nums text-white">{data.score}</p>
            </div>
          </div>

          <div className="h-2 overflow-hidden rounded-full bg-white/10">
            <div
              className={`h-full rounded-full ${barColor(data.risk)}`}
              style={{ width: `${data.score}%` }}
            />
          </div>

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
              <dt className="text-xs text-slate-500">Volatilitas (tahunan)</dt>
              <dd className="mt-1 font-semibold text-slate-100">
                {pct(data.breakdown.historical_volatility)}
              </dd>
            </div>
            <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
              <dt className="text-xs text-slate-500">ATR%</dt>
              <dd className="mt-1 font-semibold text-slate-100">{pct(data.breakdown.atr_pct)}</dd>
            </div>
            <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
              <dt className="text-xs text-slate-500">Max Drawdown</dt>
              <dd className="mt-1 font-semibold text-slate-100">
                {pct(data.breakdown.max_drawdown)}
              </dd>
            </div>
            <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
              <dt className="text-xs text-slate-500">Beta</dt>
              <dd className="mt-1 font-semibold text-slate-100">
                {data.breakdown.beta === null ? "—" : data.breakdown.beta.toFixed(2)}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </section>
  );
}
