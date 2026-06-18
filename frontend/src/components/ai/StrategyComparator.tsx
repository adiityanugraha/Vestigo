"use client";

// AI Strategy Comparator (Phase 5 Day 15) — bandingkan 2 strategi teknikal.
// GET /api/compare-strategy?a=&b=. Hanya 5 strategi teknikal tervalidasi.

import { useState } from "react";
import { getCompareStrategy, type CompareStrategyResponse } from "@/lib/api";
import { CardError } from "../CardStatus";

const TECHNICAL = ["bsjp", "bpjs", "breakout", "trend_following", "potential_reversal"];

const METRIC_LABELS: Record<string, string> = {
  cagr: "CAGR",
  sharpe_ratio: "Sharpe",
  sortino_ratio: "Sortino",
  calmar_ratio: "Calmar",
  max_drawdown: "Max Drawdown",
  winrate: "Winrate",
  profit_factor: "Profit Factor",
  recovery_factor: "Recovery Factor",
};

type State =
  | { status: "idle" | "loading" }
  | { status: "ready"; data: CompareStrategyResponse }
  | { status: "error"; error: string };

export function StrategyComparator() {
  const [a, setA] = useState("breakout");
  const [b, setB] = useState("trend_following");
  const [state, setState] = useState<State>({ status: "idle" });

  async function run() {
    setState({ status: "loading" });
    try {
      setState({ status: "ready", data: await getCompareStrategy(a, b) });
    } catch (err) {
      setState({ status: "error", error: err instanceof Error ? err.message : "Gagal memuat" });
    }
  }

  const metricKeys = (d: CompareStrategyResponse) =>
    Array.from(new Set([...Object.keys(d.metrics_a), ...Object.keys(d.metrics_b)]));

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">AI Strategy Comparator</h2>
      <p className="mb-4 text-xs text-slate-500">
        Bandingkan dua strategi teknikal (metrik historis) + narasi tradeoff.
      </p>

      <form
        className="mb-4 flex flex-wrap items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <select
          value={a}
          onChange={(e) => setA(e.target.value)}
          className="rounded-lg border border-white/10 bg-[#0b1120] px-3 py-1.5 text-sm text-white"
        >
          {TECHNICAL.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <span className="text-slate-500">vs</span>
        <select
          value={b}
          onChange={(e) => setB(e.target.value)}
          className="rounded-lg border border-white/10 bg-[#0b1120] px-3 py-1.5 text-sm text-white"
        >
          {TECHNICAL.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={state.status === "loading"}
          className="rounded-lg border border-sky-400/40 bg-sky-500/15 px-4 py-1.5 text-sm font-medium text-sky-100 transition-colors hover:bg-sky-500/25 disabled:opacity-50"
        >
          {state.status === "loading" ? "Membandingkan…" : "Bandingkan"}
        </button>
      </form>

      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <div className="space-y-3 text-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3 text-left font-medium">Metrik</th>
                  <th className="py-2 px-3 text-right font-medium">{state.data.strategy_a}</th>
                  <th className="py-2 pl-3 text-right font-medium">{state.data.strategy_b}</th>
                </tr>
              </thead>
              <tbody>
                {metricKeys(state.data).map((k) => (
                  <tr key={k} className="border-t border-white/5">
                    <td className="py-2 pr-3 text-left text-slate-300">{METRIC_LABELS[k] ?? k}</td>
                    <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                      {state.data.metrics_a[k] ?? "-"}
                    </td>
                    <td className="py-2 pl-3 text-right tabular-nums text-slate-200">
                      {state.data.metrics_b[k] ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {state.data.comparison && <p className="text-slate-200">{state.data.comparison}</p>}
          <p className="text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
