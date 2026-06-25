"use client";

// Portfolio Builder (Phase 4). Input profil risiko + modal -> alokasi bobot.
// POST /api/portfolio-builder.

import { useState } from "react";
import { postPortfolioBuilder, type PortfolioResponse } from "@/lib/api";
import { fmtScore, fmtValue } from "@/lib/format";
import { useAsyncAction } from "@/lib/useAsyncAction";
import { RiskCapitalForm } from "../RiskCapitalForm";
import { VCard } from "../vestigo/Card";
import { CardError } from "../CardStatus";

function levelClass(level: string): string {
  if (level === "LOW") return "num-up";
  if (level === "HIGH") return "num-down";
  if (level === "MEDIUM") return "chip-warn";
  return "t2";
}

export function PortfolioBuilder() {
  const [risk, setRisk] = useState("MODERATE");
  const [capital, setCapital] = useState(100_000_000);
  const { status, data, error, run } = useAsyncAction<PortfolioResponse>();
  const build = () => run(() => postPortfolioBuilder({ risk, capital, universe: "lq45" }));

  return (
    <VCard
      title="Portfolio Builder"
      sub="Alokasi otomatis (skor + risiko + diversifikasi) sesuai profil risiko"
      subMono={false}
    >
      <RiskCapitalForm
        risk={risk}
        setRisk={setRisk}
        capital={capital}
        setCapital={setCapital}
        onSubmit={build}
        loading={status === "loading"}
        submitLabel="Bangun Portofolio"
      />

      {status === "error" && <CardError message={error} onRetry={build} />}
      {status === "ready" && (
        <>
          <div className="tile-grid-3">
            <div className="tile">
              <p className="tile-label">Posisi</p>
              <p className="tile-val mono">{data.n_positions}</p>
            </div>
            <div className="tile">
              <p className="tile-label">Risiko portofolio</p>
              <p className={`tile-val mono ${levelClass(data.summary.portfolio_risk_level)}`}>
                {data.summary.portfolio_risk_level}
              </p>
            </div>
            <div className="tile">
              <p className="tile-label">Korelasi rata²</p>
              <p className="tile-val mono">{fmtScore(data.summary.avg_correlation, 2)}</p>
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
                {data.allocations.map((a) => (
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
          <p className="disclaimer">{data.disclaimer}</p>
        </>
      )}
    </VCard>
  );
}
