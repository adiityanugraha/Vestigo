"use client";

// Portfolio Builder (Phase 4). Input profil risiko + modal -> alokasi bobot.
// POST /api/portfolio-builder.

import { useState } from "react";
import { postPortfolioBuilder, type PortfolioResponse } from "@/lib/api";
import { fmtScore, fmtValue } from "@/lib/format";
import { VCard } from "../vestigo/Card";
import { CardError } from "../CardStatus";

const PROFILES = [
  { key: "CONSERVATIVE", label: "Conservative" },
  { key: "MODERATE", label: "Moderate" },
  { key: "AGGRESSIVE", label: "Aggressive" },
];

function levelClass(level: string): string {
  if (level === "LOW") return "num-up";
  if (level === "HIGH") return "num-down";
  if (level === "MEDIUM") return "chip-warn";
  return "t2";
}

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: PortfolioResponse }
  | { status: "error"; error: string };

export function PortfolioBuilder() {
  const [risk, setRisk] = useState("MODERATE");
  const [capital, setCapital] = useState(100_000_000);
  const [state, setState] = useState<State>({ status: "idle" });

  async function build() {
    setState({ status: "loading" });
    try {
      const data = await postPortfolioBuilder({ risk, capital, universe: "lq45" });
      setState({ status: "ready", data });
    } catch (err) {
      setState({
        status: "error",
        error: err instanceof Error ? err.message : "Gagal membangun portofolio",
      });
    }
  }

  return (
    <VCard
      title="Portfolio Builder"
      sub="Alokasi otomatis (skor + risiko + diversifikasi) sesuai profil risiko"
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
        <button type="button" onClick={build} disabled={state.status === "loading"} className="primary-btn">
          {state.status === "loading" ? "Menyusun…" : "Bangun Portofolio"}
        </button>
      </div>

      {state.status === "error" && <CardError message={state.error} onRetry={build} />}
      {state.status === "ready" && (
        <>
          <div className="tile-grid-3">
            <div className="tile">
              <p className="tile-label">Posisi</p>
              <p className="tile-val mono">{state.data.n_positions}</p>
            </div>
            <div className="tile">
              <p className="tile-label">Risiko portofolio</p>
              <p className={`tile-val mono ${levelClass(state.data.summary.portfolio_risk_level)}`}>
                {state.data.summary.portfolio_risk_level}
              </p>
            </div>
            <div className="tile">
              <p className="tile-label">Korelasi rata²</p>
              <p className="tile-val mono">{fmtScore(state.data.summary.avg_correlation, 2)}</p>
            </div>
          </div>

          <div className="table-wrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Saham</th>
                  <th className="ta-r">Bobot</th>
                  <th className="ta-r">Alokasi</th>
                  <th className="ta-r">Skor</th>
                  <th className="ta-r">Risiko</th>
                </tr>
              </thead>
              <tbody>
                {state.data.allocations.map((a) => (
                  <tr key={a.ticker}>
                    <td>
                      <span className="tk-pill">{a.ticker}</span>
                      {a.sector && <span className="card-sub"> {a.sector}</span>}
                    </td>
                    <td className="ta-r mono chip-info">{fmtScore(a.weight * 100, 1)}%</td>
                    <td className="ta-r mono">{fmtValue(a.amount)}</td>
                    <td className="ta-r mono">{fmtScore(a.score, 0)}</td>
                    <td className={`ta-r mono ${levelClass(a.risk_level)}`}>{a.risk_level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="feature-note">
            Menyusun alokasi otomatis dari skor, risiko, dan korelasi sesuai profil risiko.
          </p>
          <p className="disclaimer">{state.data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
