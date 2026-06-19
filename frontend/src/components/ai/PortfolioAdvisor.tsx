"use client";

// Portfolio AI Advisor (Phase 5) — alokasi (Phase 4) + penjelasan AI.
// POST /api/portfolio-advisor.

import { useState } from "react";
import { postPortfolioAdvisor, type PortfolioAdvisorResponse } from "@/lib/api";
import { fmtScore, fmtValue } from "@/lib/format";
import { VCard } from "../vestigo/Card";
import { CardError } from "../CardStatus";

const PROFILES = [
  { key: "CONSERVATIVE", label: "Conservative" },
  { key: "MODERATE", label: "Moderate" },
  { key: "AGGRESSIVE", label: "Aggressive" },
];

function levelClass(level: string | null | undefined): string {
  if (level === "LOW") return "num-up";
  if (level === "HIGH") return "num-down";
  if (level === "MEDIUM") return "chip-warn";
  return "t2";
}

type State =
  | { status: "idle" | "loading" }
  | { status: "ready"; data: PortfolioAdvisorResponse }
  | { status: "error"; error: string };

export function PortfolioAdvisor() {
  const [risk, setRisk] = useState("MODERATE");
  const [capital, setCapital] = useState(100_000_000);
  const [state, setState] = useState<State>({ status: "idle" });

  async function run() {
    setState({ status: "loading" });
    try {
      const data = await postPortfolioAdvisor({ risk, capital, universe: "lq45" });
      setState({ status: "ready", data });
    } catch (err) {
      setState({ status: "error", error: err instanceof Error ? err.message : "Gagal memuat" });
    }
  }

  return (
    <VCard
      title="Portfolio AI Advisor"
      sub="Alokasi sesuai profil risiko + penjelasan AI tiap bobot"
      subMono={false}
    >
      <div className="cmp-row" style={{ alignItems: "flex-end" }}>
        <div>
          <p className="chip-label" style={{ marginBottom: 6 }}>
            Profil risiko
          </p>
          <div className="cmp-row">
            {PROFILES.map((p) => (
              <button
                key={p.key}
                type="button"
                onClick={() => setRisk(p.key)}
                className={`pill-chip ${risk === p.key ? "pill-on" : ""}`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <input
          type="number"
          value={capital}
          min={1_000_000}
          step={10_000_000}
          onChange={(e) => setCapital(Number(e.target.value) || 0)}
          className="field-input flex1"
          style={{ minWidth: 160 }}
          placeholder="Modal (Rp)"
        />
        <button
          type="button"
          onClick={run}
          disabled={state.status === "loading"}
          className="primary-btn"
        >
          {state.status === "loading" ? "Menyusun…" : "Sarankan Portofolio"}
        </button>
      </div>

      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <>
          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Saham</th>
                  <th className="ta-r">Bobot</th>
                  <th className="ta-r">Alokasi</th>
                  <th className="ta-r">Risiko</th>
                </tr>
              </thead>
              <tbody>
                {state.data.allocations.map((a) => (
                  <tr key={a.ticker}>
                    <td>
                      <span className="tk-pill">{a.ticker}</span>
                    </td>
                    <td className="ta-r mono chip-info">{fmtScore(a.weight * 100, 1)}%</td>
                    <td className="ta-r mono">{a.amount != null ? fmtValue(a.amount) : "—"}</td>
                    <td className={`ta-r mono ${levelClass(a.risk_level)}`}>
                      {a.risk_level ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {state.data.explanation && (
            <p className="narrator" style={{ fontSize: 14 }}>{state.data.explanation}</p>
          )}
          <p className="disclaimer">{state.data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
