"use client";

// AI Analyst (Phase 5 Day 15) — narasi AI ter-grounding per saham.
// Input ticker -> GET /api/ai-analysis/{ticker}.

import { useState } from "react";
import { getAiAnalysis, type AiAnalysisResponse } from "@/lib/api";
import { CardError } from "../CardStatus";

type State =
  | { status: "idle" | "loading" }
  | { status: "ready"; data: AiAnalysisResponse }
  | { status: "error"; error: string };

export function AIAnalysis() {
  const [ticker, setTicker] = useState("BBCA");
  const [state, setState] = useState<State>({ status: "idle" });

  async function run() {
    setState({ status: "loading" });
    try {
      setState({ status: "ready", data: await getAiAnalysis(ticker) });
    } catch (err) {
      setState({ status: "error", error: err instanceof Error ? err.message : "Gagal memuat" });
    }
  }

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">AI Analyst</h2>
      <p className="mb-4 text-xs text-slate-500">
        Ringkasan, faktor bullish & risiko, confidence — angka dari sistem, dinarasikan AI.
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
          {state.status === "loading" ? "Menganalisis…" : "Analisis"}
        </button>
      </form>

      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3">
            <span className="text-lg font-semibold text-white">{state.data.ticker}</span>
            {state.data.confidence != null && (
              <span className="rounded-md border border-sky-400/30 bg-sky-500/10 px-2 py-0.5 text-xs text-sky-200">
                Confidence {state.data.confidence}
              </span>
            )}
            {state.data.date && <span className="text-xs text-slate-500">{state.data.date}</span>}
          </div>

          {state.data.summary && <p className="text-slate-200">{state.data.summary}</p>}
          {state.data.note && <p className="text-xs text-amber-300/80">{state.data.note}</p>}

          {state.data.bullish_factors.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-300">Bullish</p>
              <ul className="mt-1 space-y-1">
                {state.data.bullish_factors.map((f, i) => (
                  <li key={i} className="text-slate-300">+ {f}</li>
                ))}
              </ul>
            </div>
          )}
          {state.data.risk_factors.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-rose-300">Risiko</p>
              <ul className="mt-1 space-y-1">
                {state.data.risk_factors.map((f, i) => (
                  <li key={i} className="text-slate-300">- {f}</li>
                ))}
              </ul>
            </div>
          )}
          <p className="text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
