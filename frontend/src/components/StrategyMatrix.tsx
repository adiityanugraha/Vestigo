"use client";

// Strategy Comparison Dashboard (Phase 3 Day 14).
// Matrix saham x 9 strategi dari GET /api/strategy-matrix. Sel tiga-keadaan:
//   V (lolos) / x (dinilai tapi gagal) / – (tidak dinilai, mis. tanpa data
//   fundamental) — meneruskan distingsi evaluated-vs-failed dari backend.

import { useState } from "react";
import { getStrategyMatrix, type StrategyMeta } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

// Singkatan kolom agar matrix muat; nama lengkap tampil sebagai tooltip.
const SHORT_LABELS: Record<string, string> = {
  bsjp: "BSJP",
  bpjs: "BPJS",
  breakout: "BRK",
  trend_following: "TRND",
  potential_reversal: "RVSL",
  high_growth: "GRWT",
  cash_rich: "CASH",
  turnaround: "TURN",
  timeless: "TMLS",
};

function shortLabel(strategy: StrategyMeta): string {
  return SHORT_LABELS[strategy.key] ?? strategy.key.slice(0, 4).toUpperCase();
}

function Cell({ value }: { value: boolean | null }) {
  if (value === true) {
    return (
      <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-emerald-500/20 text-xs font-bold text-emerald-300">
        V
      </span>
    );
  }
  if (value === false) {
    return (
      <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-white/[0.04] text-xs text-slate-600">
        x
      </span>
    );
  }
  return (
    <span
      className="inline-flex h-6 w-6 items-center justify-center rounded-md text-xs text-slate-700"
      title="Tidak dinilai (data tidak cukup)"
    >
      –
    </span>
  );
}

export function StrategyMatrix() {
  const [minPassed, setMinPassed] = useState(1);
  const { status, data, error, reload } = useApi(
    () => getStrategyMatrix(minPassed),
    [minPassed],
  );

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Strategy Comparison Matrix</h2>
        <div className="flex items-center gap-2">
          {data && <CachedBadge cached={data.cached} />}
          <span className="text-xs font-medium text-slate-400">{data?.date ?? ""}</span>
        </div>
      </div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-500">
          Saham lolos di strategi mana saja (V lolos · x gagal · – tak dinilai)
        </p>
        <label className="flex items-center gap-2 text-xs text-slate-400">
          Min. lolos
          <select
            className="rounded-md border border-white/10 bg-[#0b1020] px-2 py-1 text-xs text-slate-200"
            onChange={(event) => setMinPassed(Number(event.target.value))}
            value={minPassed}
          >
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>
                {n} strategi
              </option>
            ))}
          </select>
        </label>
      </div>

      {status === "loading" && <CardSkeleton lines={7} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="overflow-x-auto">
          {data.matrix.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">
              Tidak ada saham yang lolos ≥ {minPassed} strategi.
            </p>
          ) : (
            <table className="w-full min-w-[640px] border-separate border-spacing-y-1 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="px-2 py-1">Ticker</th>
                  <th className="px-2 py-1 text-center">#</th>
                  {data.strategies.map((strategy) => (
                    <th
                      className={`px-1 py-1 text-center ${
                        strategy.type === "fundamental" ? "text-amber-300/80" : "text-sky-300/80"
                      }`}
                      key={strategy.key}
                      title={strategy.name}
                    >
                      {shortLabel(strategy)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.matrix.map((row) => (
                  <tr className="rounded-lg bg-white/[0.02]" key={row.ticker}>
                    <td className="px-2 py-1.5">
                      <span className="font-semibold text-slate-100">{row.ticker}</span>
                      {row.name && (
                        <span className="ml-2 hidden text-xs text-slate-500 xl:inline">
                          {row.name}
                        </span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-center font-bold tabular-nums text-emerald-300">
                      {row.passed_count}
                    </td>
                    {data.strategies.map((strategy) => (
                      <td className="px-1 py-1.5 text-center" key={strategy.key}>
                        <Cell value={row.results[strategy.key] ?? null} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="mt-3 text-[11px] text-slate-500">
            <span className="text-sky-300/80">biru</span> = teknikal ·{" "}
            <span className="text-amber-300/80">kuning</span> = fundamental ·{" "}
            {data.universe_evaluated} saham dievaluasi
          </p>
        </div>
      )}
    </section>
  );
}
