"use client";

import { getScreener } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { VCard } from "./vestigo/Card";
import { CardError } from "./CardStatus";
import { ScreenerTable, toScreenerRow } from "./ScreenerTable";

type PredictionPanelProps = {
  onSelectSymbol: (symbol: string) => void;
  selectedSymbol: string;
};

export function PredictionPanel({ onSelectSymbol, selectedSymbol }: PredictionPanelProps) {
  const { status, data, error, reload } = useApi(() => getScreener(5, true), []);

  const bsjp = data ? data.bsjp.map(toScreenerRow) : [];
  const bpjs = data ? data.bpjs.map(toScreenerRow) : [];

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
