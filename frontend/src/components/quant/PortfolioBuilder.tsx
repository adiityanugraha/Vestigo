"use client";

// Portfolio Builder (Phase 4 Day 15).
// Input profil risiko + modal -> POST /api/portfolio-builder -> alokasi bobot.

import { useState } from "react";
import { postPortfolioBuilder, type PortfolioResponse } from "@/lib/api";
import { CardError } from "../CardStatus";

const PROFILES = [
  { key: "CONSERVATIVE", label: "Conservative" },
  { key: "MODERATE", label: "Moderate" },
  { key: "AGGRESSIVE", label: "Aggressive" },
];

const LEVEL_TONE: Record<string, string> = {
  LOW: "text-emerald-300",
  MEDIUM: "text-amber-300",
  HIGH: "text-rose-300",
};

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
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">Portfolio Builder</h2>
      <p className="mb-4 text-xs text-slate-500">
        Susun alokasi otomatis (skor + risiko + diversifikasi) sesuai profil risiko.
      </p>

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div>
          <p className="mb-1 text-xs text-slate-400">Profil risiko</p>
          <div className="flex gap-2">
            {PROFILES.map((p) => (
              <button
                key={p.key}
                type="button"
                onClick={() => setRisk(p.key)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  risk === p.key
                    ? "border-sky-400/40 bg-sky-500/15 text-sky-200"
                    : "border-white/10 text-slate-400 hover:bg-white/5"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-1 text-xs text-slate-400">Modal (Rp)</p>
          <input
            type="number"
            value={capital}
            min={1_000_000}
            step={10_000_000}
            onChange={(e) => setCapital(Number(e.target.value) || 0)}
            className="w-44 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-sm text-white"
          />
        </div>
        <button
          type="button"
          onClick={build}
          disabled={state.status === "loading"}
          className="rounded-lg border border-sky-400/40 bg-sky-500/15 px-4 py-1.5 text-sm font-medium text-sky-100 transition-colors hover:bg-sky-500/25 disabled:opacity-50"
        >
          {state.status === "loading" ? "Menyusun…" : "Bangun Portofolio"}
        </button>
      </div>

      {state.status === "error" && (
        <CardError message={state.error} onRetry={build} />
      )}
      {state.status === "ready" && (
        <>
          <div className="mb-3 flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span className="text-slate-400">
              Posisi: <span className="font-semibold text-white">{state.data.n_positions}</span>
            </span>
            <span className="text-slate-400">
              Risiko portofolio:{" "}
              <span
                className={`font-semibold ${
                  LEVEL_TONE[state.data.summary.portfolio_risk_level] ?? "text-slate-200"
                }`}
              >
                {state.data.summary.portfolio_risk_level}
              </span>
            </span>
            <span className="text-slate-400">
              Korelasi rata²:{" "}
              <span className="font-semibold text-white">
                {state.data.summary.avg_correlation.toFixed(2)}
              </span>
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3 text-left font-medium">Saham</th>
                  <th className="py-2 px-3 text-right font-medium">Bobot</th>
                  <th className="py-2 px-3 text-right font-medium">Alokasi</th>
                  <th className="py-2 px-3 text-right font-medium">Skor</th>
                  <th className="py-2 pl-3 text-right font-medium">Risiko</th>
                </tr>
              </thead>
              <tbody>
                {state.data.allocations.map((a) => (
                  <tr key={a.ticker} className="border-t border-white/5">
                    <td className="py-2 pr-3 text-left">
                      <span className="font-medium text-white">{a.ticker}</span>
                      {a.sector && (
                        <span className="ml-2 text-xs text-slate-500">{a.sector}</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-right tabular-nums text-sky-200">
                      {(a.weight * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                      Rp {a.amount.toLocaleString("id-ID")}
                    </td>
                    <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                      {a.score.toFixed(0)}
                    </td>
                    <td className={`py-2 pl-3 text-right font-medium ${LEVEL_TONE[a.risk_level] ?? "text-slate-300"}`}>
                      {a.risk_level}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </>
      )}
    </section>
  );
}
