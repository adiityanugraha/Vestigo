"use client";

import { getScreener, type ScreenerCandidate } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError } from "./CardStatus";
import { ScreenerTable, type ScreenerRow } from "./ScreenerTable";

type PredictionPanelProps = {
  onSelectSymbol: (symbol: string) => void;
  selectedSymbol: string;
};

function toRow(candidate: ScreenerCandidate): ScreenerRow {
  return {
    symbol: candidate.ticker,
    strategy: candidate.strategy,
    probabilityUp: candidate.prediction?.probability_up ?? 0,
    entry: candidate.levels.entry,
    stopLoss: candidate.levels.stop_loss,
    takeProfit: candidate.levels.take_profit,
    exit: candidate.levels.exit,
    value: candidate.value,
  };
}

export function PredictionPanel({ onSelectSymbol, selectedSymbol }: PredictionPanelProps) {
  const { status, data, error, reload } = useApi(() => getScreener(5, true), []);

  const bsjp = data ? data.bsjp.map(toRow) : [];
  const bpjs = data ? data.bpjs.map(toRow) : [];

  return (
    <section className="flex flex-col gap-6">
      <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-base font-semibold text-white">ML Screener</h2>
            <p className="mt-1 text-sm text-slate-400">
              Dihitung server-side: data, indikator, ONNX inference, ranking
            </p>
          </div>
          <div className="flex items-center gap-2">
            {data && <CachedBadge cached={data.cached} />}
            <span className="rounded-md border border-white/10 px-3 py-1 text-xs font-medium text-slate-300">
              {status}
            </span>
          </div>
        </div>

        {status === "error" && (
          <div className="mt-5">
            <CardError message={error} onRetry={reload} />
          </div>
        )}

        {status === "ready" && data && (
          <div className="mt-4 grid gap-3 text-sm text-slate-300 sm:grid-cols-4">
            <p>{data.universe} saham di universe</p>
            <p>{data.screened} kandidat lolos</p>
            <p>{data.bsjp.length} BSJP ranked</p>
            <p>{data.bpjs.length} BPJS ranked</p>
          </div>
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <ScreenerTable
          isLoading={status === "loading"}
          onSelectSymbol={onSelectSymbol}
          selectedSymbol={selectedSymbol}
          title="Top 5 BSJP"
          rows={bsjp}
        />
        <ScreenerTable
          isLoading={status === "loading"}
          onSelectSymbol={onSelectSymbol}
          selectedSymbol={selectedSymbol}
          title="Top 5 BPJS"
          rows={bpjs}
        />
      </div>
    </section>
  );
}
