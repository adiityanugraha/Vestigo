"use client";

// AI Strategy Comparator (Phase 5) — bandingkan 2 strategi teknikal.
// GET /api/compare-strategy?a=&b=. Hanya 5 strategi teknikal tervalidasi.

import { useState } from "react";
import { getCompareStrategy, type CompareStrategyResponse } from "@/lib/api";
import { VCard } from "../vestigo/Card";
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
    <VCard
      title="AI Strategy Comparator"
      sub="Bandingkan dua strategi teknikal (metrik historis) + narasi tradeoff"
      subMono={false}
    >
      <form
        className="cmp-row"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <select value={a} onChange={(e) => setA(e.target.value)} className="select">
          {TECHNICAL.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <span className="t3">vs</span>
        <select value={b} onChange={(e) => setB(e.target.value)} className="select">
          {TECHNICAL.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <button type="submit" disabled={state.status === "loading"} className="primary-btn">
          {state.status === "loading" ? "Membandingkan…" : "Bandingkan"}
        </button>
      </form>

      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <>
          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Metrik</th>
                  <th className="ta-r">{state.data.strategy_a}</th>
                  <th className="ta-r">{state.data.strategy_b}</th>
                </tr>
              </thead>
              <tbody>
                {metricKeys(state.data).map((k) => (
                  <tr key={k}>
                    <td className="t2">{METRIC_LABELS[k] ?? k}</td>
                    <td className="ta-r mono">{state.data.metrics_a[k] ?? "—"}</td>
                    <td className="ta-r mono">{state.data.metrics_b[k] ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {state.data.comparison && <p className="narrator" style={{ fontSize: 14 }}>{state.data.comparison}</p>}
          <p className="feature-note">
            Membandingkan metrik historis dua strategi teknikal untuk melihat tradeoff
            imbal hasil & risiko.
          </p>
          <p className="disclaimer">{state.data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
