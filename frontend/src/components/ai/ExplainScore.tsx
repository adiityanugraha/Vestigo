"use client";

// Explainable AI 2.0 (Phase 5) — breakdown pembentukan Composite Score.
// Input ticker -> GET /api/explain-score/{ticker}.

import { useState } from "react";
import { getExplainScore, type ExplainScoreResponse } from "@/lib/api";
import { fmtScore } from "@/lib/format";
import { VCard } from "../vestigo/Card";
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
    <VCard
      title="Explainable AI 2.0"
      sub="Kontribusi tiap komponen Composite Score + narasi"
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
          placeholder="mis. BBRI"
        />
        <button type="submit" disabled={state.status === "loading"} className="primary-btn">
          {state.status === "loading" ? "Memuat…" : "Jelaskan"}
        </button>
      </form>

      {state.status === "idle" && (
        <p className="empty-state">
          Uraikan kontribusi Tech / Momentum / ML terhadap Composite Score.
        </p>
      )}
      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <>
          <div className="card-head">
            <span className="card-title">{state.data.ticker}</span>
            <div className="cmp-row">
              {state.data.overall_score != null && (
                <span className="badge badge-info badge-full">
                  Score {state.data.overall_score}
                </span>
              )}
              {!state.data.ml_available && (
                <span className="small chip-warn">ML tak tersedia (bobot direnormalisasi)</span>
              )}
            </div>
          </div>

          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Komponen</th>
                  <th className="ta-r">Skor</th>
                  <th className="ta-r">Bobot</th>
                  <th className="ta-r">Kontribusi</th>
                </tr>
              </thead>
              <tbody>
                {state.data.breakdown.map((c) => (
                  <tr key={c.component}>
                    <td>{c.label}</td>
                    <td className="ta-r mono">{c.score}</td>
                    <td className="ta-r mono t2">{fmtScore(c.effective_weight * 100, 0)}%</td>
                    <td className="ta-r mono chip-info">{c.contribution}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {state.data.summary && <p className="narrator" style={{ fontSize: 14 }}>{state.data.summary}</p>}
          <p className="feature-note">
            Menjabarkan kontribusi tiap komponen (teknikal, momentum, ML) terhadap
            Composite Score saham.
          </p>
          <p className="disclaimer">{state.data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
