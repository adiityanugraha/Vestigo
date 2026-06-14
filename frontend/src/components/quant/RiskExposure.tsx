"use client";

// Risk Exposure per strategi (Phase 4 Day 15).
// Tabel profil risiko 5 strategi tervalidasi dari GET /api/risk-profile/{s}
// (vol, beta, max DD, losing streak, klasifikasi Low/Medium/High).

import { getRiskProfile, type RiskProfileResponse } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "../CardStatus";

const STRATEGIES = ["bsjp", "bpjs", "breakout", "trend_following", "potential_reversal"];

const LEVEL_TONE: Record<string, string> = {
  LOW: "bg-emerald-500/15 text-emerald-300",
  MEDIUM: "bg-amber-500/15 text-amber-300",
  HIGH: "bg-rose-500/15 text-rose-300",
};

function pct(value: number): string {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
}

export function RiskExposure() {
  const { status, data, error, reload } = useApi(
    () => Promise.all(STRATEGIES.map((s) => getRiskProfile(s))),
    [],
  );

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">Risk Exposure</h2>
      <p className="mb-4 text-xs text-slate-500">
        Profil risiko per strategi (berbeda dari Risk Meter per-saham).
      </p>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-3 text-left font-medium">Strategi</th>
                <th className="py-2 px-3 text-right font-medium">Volatilitas</th>
                <th className="py-2 px-3 text-right font-medium">Beta</th>
                <th className="py-2 px-3 text-right font-medium">Max DD</th>
                <th className="py-2 px-3 text-right font-medium">Streak</th>
                <th className="py-2 pl-3 text-right font-medium">Risiko</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r: RiskProfileResponse) => (
                <tr key={r.strategy} className="border-t border-white/5">
                  <td className="py-2 pr-3 text-left text-white">{r.name ?? r.strategy}</td>
                  <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                    {(r.volatility * 100).toFixed(1)}%
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                    {r.beta.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-rose-300/90">
                    {pct(r.max_drawdown)}
                  </td>
                  <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                    {r.losing_streak}
                  </td>
                  <td className="py-2 pl-3 text-right">
                    <span
                      className={`rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                        LEVEL_TONE[r.risk_level] ?? "bg-white/5 text-slate-300"
                      }`}
                    >
                      {r.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data[0]?.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
