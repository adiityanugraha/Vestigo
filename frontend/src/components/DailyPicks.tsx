"use client";

// Pick harian Top 5 BSJP / BPJS (Screener Lite). Tabel deterministik dari
// GET /api/screener — tanpa ringkasan ML Screener (itu khusus Pro).

import { getScreener, type ScreenerCandidate } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { ScreenerTable, type ScreenerRow } from "./ScreenerTable";

type DailyPicksProps = {
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

export function DailyPicks({ onSelectSymbol, selectedSymbol }: DailyPicksProps) {
  const { status, data } = useApi(() => getScreener(5, true), []);
  const loading = status === "loading";

  return (
    <div className="grid-2">
      <ScreenerTable
        isLoading={loading}
        onSelectSymbol={onSelectSymbol}
        selectedSymbol={selectedSymbol}
        title="Top 5 BSJP"
        rows={data ? data.bsjp.map(toRow) : []}
      />
      <ScreenerTable
        isLoading={loading}
        onSelectSymbol={onSelectSymbol}
        selectedSymbol={selectedSymbol}
        title="Top 5 BPJS"
        rows={data ? data.bpjs.map(toRow) : []}
      />
    </div>
  );
}
