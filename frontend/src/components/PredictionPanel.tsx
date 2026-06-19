"use client";

import { getScreener, type ScreenerCandidate } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { VCard } from "./vestigo/Card";
import { CardError } from "./CardStatus";
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
    <>
      <VCard
        title="ML Screener"
        sub="Server-side: data, indikator, ONNX inference, ranking"
        subMono={false}
        cached={!!data?.cached}
      >
        {status === "error" && <CardError message={error} onRetry={reload} />}
        {status === "ready" && data && (
          <div className="ml-summary">
            <div className="tile">
              <p className="tile-label">Universe</p>
              <p className="tile-val mono">{data.universe} saham</p>
            </div>
            <div className="tile">
              <p className="tile-label">Kandidat lolos</p>
              <p className="tile-val mono">{data.screened} saham</p>
            </div>
            <div className="tile">
              <p className="tile-label">BSJP ranked</p>
              <p className="tile-val mono">{data.bsjp.length}</p>
            </div>
            <div className="tile">
              <p className="tile-label">BPJS ranked</p>
              <p className="tile-val mono">{data.bpjs.length}</p>
            </div>
          </div>
        )}
      </VCard>

      <div className="grid-2">
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
    </>
  );
}
