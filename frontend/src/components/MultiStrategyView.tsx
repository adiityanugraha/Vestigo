"use client";

// Multi-Strategy Engine view (Phase 3 Day 14).
// Pemilih 9 strategi (chips, dari GET /api/strategies) -> kandidat strategi
// terpilih (GET /api/screener?strategy=) dengan matched_criteria, + Strategy
// Comparison Matrix di bawahnya.

import { useState } from "react";
import {
  getStrategies,
  getStrategyScreener,
  type StrategyCandidate,
  type StrategyMeta,
} from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { DashboardShell } from "./DashboardShell";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";
import { StrategyMatrix } from "./StrategyMatrix";

function formatIdr(value: number): string {
  if (value >= 1e12) return `${(value / 1e12).toFixed(1)} T`;
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)} M`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)} jt`;
  return value.toLocaleString("id-ID");
}

function StrategyChips({
  strategies,
  selected,
  onSelect,
}: {
  strategies: StrategyMeta[];
  selected: string;
  onSelect: (key: string) => void;
}) {
  const technical = strategies.filter((s) => s.type === "technical");
  const fundamental = strategies.filter((s) => s.type === "fundamental");

  const chip = (strategy: StrategyMeta) => (
    <button
      className={`shrink-0 rounded-full border px-3 py-1.5 text-sm transition-colors ${
        strategy.key === selected
          ? "border-sky-300/50 bg-sky-500/20 font-semibold text-sky-100"
          : "border-white/10 bg-white/[0.04] text-slate-300 hover:border-white/25 hover:text-white"
      }`}
      key={strategy.key}
      onClick={() => onSelect(strategy.key)}
      type="button"
    >
      {strategy.name}
    </button>
  );

  return (
    <div className="space-y-3">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-sky-300/80">
          Teknikal
        </p>
        <div className="flex flex-wrap gap-2">{technical.map(chip)}</div>
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-300/80">
          Fundamental
        </p>
        <div className="flex flex-wrap gap-2">{fundamental.map(chip)}</div>
      </div>
    </div>
  );
}

function CandidateCard({ candidate }: { candidate: StrategyCandidate }) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="flex items-baseline justify-between gap-2">
        <div>
          <span className="text-base font-semibold text-white">{candidate.ticker}</span>
          {candidate.name && (
            <span className="ml-2 text-xs text-slate-500">{candidate.name}</span>
          )}
        </div>
        <div className="text-right text-sm">
          <p className="font-semibold tabular-nums text-slate-100">
            {candidate.close?.toLocaleString("id-ID") ?? "—"}
          </p>
          <p className="text-[11px] text-slate-500">
            Nilai Rp {formatIdr(candidate.value)}
          </p>
        </div>
      </div>
      <ul className="mt-3 space-y-1">
        {candidate.matched_criteria.map((reason) => (
          <li className="flex gap-2 text-xs text-slate-300" key={reason}>
            <span className="text-emerald-300">+</span>
            <span>{reason}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

function StrategyResults({ strategyKey }: { strategyKey: string }) {
  const { status, data, error, reload } = useApi(
    () => getStrategyScreener(strategyKey, 10),
    [strategyKey],
  );

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">
          {data?.output_label ?? "Hasil Screening"}
        </h2>
        <div className="flex items-center gap-2">
          {data && <CachedBadge cached={data.cached} />}
          {data && (
            <span className="text-xs font-medium text-slate-400">
              {data.passed} lolos / {data.evaluated} dievaluasi
            </span>
          )}
        </div>
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Kandidat beserta kriteria yang benar-benar lolos (urut nilai transaksi)
      </p>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div>
          {data.candidates.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">
              Tidak ada saham yang lolos strategi ini hari ini.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {data.candidates.map((candidate) => (
                <CandidateCard candidate={candidate} key={candidate.ticker} />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export function MultiStrategyView() {
  const [selected, setSelected] = useState("breakout");
  const strategies = useApi(() => getStrategies(), []);

  return (
    <DashboardShell
      activeNav="Strategies"
      eyebrow="Multi-Strategy Engine"
      title="Strategies"
    >
      <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
        <h2 className="mb-1 text-base font-semibold text-white">Pilih Strategi</h2>
        <p className="mb-4 text-xs text-slate-500">
          9 strategi screening — 5 teknikal & 4 fundamental
        </p>
        {strategies.status === "loading" && <CardSkeleton lines={3} />}
        {strategies.status === "error" && (
          <CardError message={strategies.error} onRetry={strategies.reload} />
        )}
        {strategies.status === "ready" && strategies.data && (
          <StrategyChips
            onSelect={setSelected}
            selected={selected}
            strategies={strategies.data}
          />
        )}
      </section>

      <StrategyResults strategyKey={selected} />

      <StrategyMatrix />
    </DashboardShell>
  );
}
