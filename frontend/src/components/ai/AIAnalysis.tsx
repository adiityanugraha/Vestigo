"use client";

// AI Analyst (Phase 5) — narasi AI ter-grounding per saham.
// Input ticker -> GET /api/ai-analysis/{ticker}.

import { useState } from "react";
import { getAiAnalysis, type AiAnalysisResponse } from "@/lib/api";
import { VCard } from "../vestigo/Card";
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
    <VCard
      title="AI Analyst per-saham"
      sub="Ringkasan + faktor — angka dari sistem, dinarasikan AI"
      subMono={false}
    >
      <form
        className="field"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          className="field-input"
          placeholder="mis. BBCA"
        />
        <button type="submit" disabled={state.status === "loading"} className="primary-btn">
          {state.status === "loading" ? "Menganalisis…" : "Analisis"}
        </button>
      </form>

      {state.status === "idle" && (
        <p className="empty-state">Masukkan ticker untuk analisis teknikal + naratif.</p>
      )}
      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <>
          <div className="card-head">
            <span className="card-title">{state.data.ticker}</span>
            <div className="cmp-row">
              {state.data.confidence != null && (
                <span className="badge badge-info badge-full">
                  Confidence {state.data.confidence}
                </span>
              )}
              {state.data.date && <span className="t3 small mono">{state.data.date}</span>}
            </div>
          </div>
          {state.data.summary && <p className="narrator" style={{ fontSize: 14 }}>{state.data.summary}</p>}
          {state.data.note && <p className="small chip-warn">{state.data.note}</p>}

          {state.data.bullish_factors.length > 0 && (
            <div>
              <p className="section-label">Faktor bullish</p>
              <ul className="factor-list">
                {state.data.bullish_factors.map((f, i) => (
                  <li key={i}>
                    <span className="fi fi-up">↑</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {state.data.risk_factors.length > 0 && (
            <div>
              <p className="section-label">Faktor risiko</p>
              <ul className="factor-list">
                {state.data.risk_factors.map((f, i) => (
                  <li key={i}>
                    <span className="fi fi-down">!</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <p className="feature-note">
            Analisis satu saham — ringkasan, faktor bullish & risiko — dengan confidence
            dari Composite Score sistem.
          </p>
          <p className="disclaimer">{state.data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
