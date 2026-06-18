"use client";

// Explainable AI 2.0 (Phase 5 Day 15) — breakdown pembentukan Composite Score.
// Input ticker -> GET /api/explain-score/{ticker}.

import { useState } from "react";
import { getExplainScore, type ExplainScoreResponse } from "@/lib/api";
import { CardError } from "../CardStatus";

type State =
  | { status: "idle" | "loading" }
  | { status: "ready"; data: ExplainScoreResponse }
  | { status: "error"; error: string };

export function ExplainScore() {
  const [ticker, setTicker] = useState("BBCA");
  const [state, setState] = useState<State>({ status: "idle" });

  async function run() {
    setState({ status: "loading" });
    try {
      setState({ status: "ready", data: await getExplainScore(ticker) });
    } catch (err) {
      setState({ status: "error", error: err instanceof Error ? err.message : "Gagal memuat" });
    }
  }

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">Explainable AI 2.0</h2>
      <p className="mb-4 text-xs text-slate-500">
        Bagaimana Composite Score terbentuk: kontribusi tiap komponen + narasi.
      </p>

      <form
        className="mb-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          className="w-32 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-sm text-white"
          placeholder="BBCA"
        />
        <button
          type="submit"
          disabled={state.status === "loading"}
          className="rounded-lg border border-sky-400/40 bg-sky-500/15 px-4 py-1.5 text-sm font-medium text-sky-100 transition-colors hover:bg-sky-500/25 disabled:opacity-50"
        >
          {state.status === "loading" ? "Memuat…" : "Jelaskan"}
        </button>
      </form>

      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3">
            <span className="text-lg font-semibold text-white">{state.data.ticker}</span>
            {state.data.overall_score != null && (
              <span className="rounded-md border border-sky-400/30 bg-sky-500/10 px-2 py-0.5 text-xs text-sky-200">
                Score {state.data.overall_score}
              </span>
            )}
            {!state.data.ml_available && (
              <span className="text-[11px] text-amber-300/80">ML tak tersedia (bobot direnormalisasi)</span>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3 text-left font-medium">Komponen</th>
                  <th className="py-2 px-3 text-right font-medium">Skor</th>
                  <th className="py-2 px-3 text-right font-medium">Bobot</th>
                  <th className="py-2 pl-3 text-right font-medium">Kontribusi</th>
                </tr>
              </thead>
              <tbody>
                {state.data.breakdown.map((c) => (
                  <tr key={c.component} className="border-t border-white/5">
                    <td className="py-2 pr-3 text-left text-slate-200">{c.label}</td>
                    <td className="py-2 px-3 text-right tabular-nums text-slate-200">{c.score}</td>
                    <td className="py-2 px-3 text-right tabular-nums text-slate-400">
                      {(c.effective_weight * 100).toFixed(0)}%
                    </td>
                    <td className="py-2 pl-3 text-right tabular-nums text-sky-200">{c.contribution}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {state.data.summary && <p className="text-slate-200">{state.data.summary}</p>}
          <p className="text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
