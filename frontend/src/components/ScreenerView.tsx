"use client";

import { useState } from "react";
import { AiReportCard } from "./AiReportCard";
import { CandlestickChart } from "./CandlestickChart";
import { CompositeScoreCard } from "./CompositeScoreCard";
import { DashboardShell } from "./DashboardShell";
import { ExplainPanel } from "./ExplainPanel";
import { ForecastCard } from "./ForecastCard";
import { MarketBreadthCard } from "./MarketBreadthCard";
import { useMode } from "./ModeProvider";
import { PredictionPanel } from "./PredictionPanel";
import { RiskMeterCard } from "./RiskMeterCard";
import { ScreenerHistoryCard } from "./ScreenerHistoryCard";
import { StrengthBadge } from "./StrengthBadge";
import { SupportResistanceCard } from "./SupportResistanceCard";

// Page Screener.
// Lite = Market Breadth (breadth + gainers/losers + heatmap sektor).
// Pro  = + ML/Composite screener, analitik per-saham terpilih, forecast,
//         strength, explainable AI, dan riwayat screener.
export function ScreenerView() {
  const { pro } = useMode();
  const [selectedSymbol, setSelectedSymbol] = useState("BBCA");

  return (
    <DashboardShell activeNav="Screener" eyebrow="IDX Daily Screener" title="Screener">
      <MarketBreadthCard />

      {pro && (
        <>
          <PredictionPanel
            onSelectSymbol={setSelectedSymbol}
            selectedSymbol={selectedSymbol}
          />

          {/* Analisis saham terpilih dari tabel di atas */}
          <CandlestickChart symbol={selectedSymbol} />

          <div className="grid-3">
            <AiReportCard symbol={selectedSymbol} />
            <RiskMeterCard symbol={selectedSymbol} />
            <SupportResistanceCard symbol={selectedSymbol} />
          </div>

          <div className="grid-2">
            <ForecastCard symbol={selectedSymbol} />
            <StrengthBadge symbol={selectedSymbol} />
          </div>

          <ExplainPanel symbol={selectedSymbol} />

          <div className="grid-2">
            <CompositeScoreCard
              onSelectSymbol={setSelectedSymbol}
              selectedSymbol={selectedSymbol}
            />
            <ScreenerHistoryCard />
          </div>
        </>
      )}
    </DashboardShell>
  );
}
