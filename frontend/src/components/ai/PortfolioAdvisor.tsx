"use client";

// Portfolio AI Advisor (Phase 5 Day 15) — alokasi (Phase 4) + penjelasan AI.
// POST /api/portfolio-advisor.

import { useState } from "react";
import { postPortfolioAdvisor, type PortfolioAdvisorResponse } from "@/lib/api";
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
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <h2 className="mb-1 text-base font-semibold text-white">Portfolio AI Advisor</h2>
      <p className="mb-4 text-xs text-slate-500">
        Alokasi sesuai profil risiko + penjelasan AI kenapa tiap bobot. Bukan nasihat keuangan.
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
          onClick={run}
          disabled={state.status === "loading"}
          className="rounded-lg border border-sky-400/40 bg-sky-500/15 px-4 py-1.5 text-sm font-medium text-sky-100 transition-colors hover:bg-sky-500/25 disabled:opacity-50"
        >
          {state.status === "loading" ? "Menyusun…" : "Sarankan Portofolio"}
        </button>
      </div>

      {state.status === "error" && <CardError message={state.error} onRetry={run} />}
      {state.status === "ready" && (
        <div className="space-y-3">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3 text-left font-medium">Saham</th>
                  <th className="py-2 px-3 text-right font-medium">Bobot</th>
                  <th className="py-2 px-3 text-right font-medium">Alokasi</th>
                  <th className="py-2 pl-3 text-right font-medium">Risiko</th>
                </tr>
              </thead>
              <tbody>
                {state.data.allocations.map((a) => (
                  <tr key={a.ticker} className="border-t border-white/5">
                    <td className="py-2 pr-3 text-left font-medium text-white">{a.ticker}</td>
                    <td className="py-2 px-3 text-right tabular-nums text-sky-200">
                      {(a.weight * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-3 text-right tabular-nums text-slate-200">
                      {a.amount != null ? `Rp ${a.amount.toLocaleString("id-ID")}` : "-"}
                    </td>
                    <td className={`py-2 pl-3 text-right font-medium ${LEVEL_TONE[a.risk_level ?? ""] ?? "text-slate-300"}`}>
                      {a.risk_level ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {state.data.explanation && <p className="text-sm text-slate-200">{state.data.explanation}</p>}
          <p className="text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
