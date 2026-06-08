"use client";

import { useState } from "react";
import { AiReportCard } from "./AiReportCard";
import { CandlestickChart } from "./CandlestickChart";
import { CompositeScoreCard } from "./CompositeScoreCard";
import { DashboardShell } from "./DashboardShell";
import { MarketBreadthCard } from "./MarketBreadthCard";
import { PredictionPanel } from "./PredictionPanel";
import { RiskMeterCard } from "./RiskMeterCard";
import { ScreenerHistoryCard } from "./ScreenerHistoryCard";
import { SupportResistanceCard } from "./SupportResistanceCard";

export function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState("BBCA");

  return (
    <DashboardShell>
      <section className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
        <CandlestickChart symbol={selectedSymbol} />
        <MarketBreadthCard />
      </section>

      {/* Analisis per-saham terpilih (backend Phase 2) */}
      <section className="grid gap-6 lg:grid-cols-3">
        <AiReportCard symbol={selectedSymbol} />
        <RiskMeterCard symbol={selectedSymbol} />
        <SupportResistanceCard symbol={selectedSymbol} />
      </section>

      <PredictionPanel
        onSelectSymbol={setSelectedSymbol}
        selectedSymbol={selectedSymbol}
      />

      <section className="grid gap-6 xl:grid-cols-2">
        <CompositeScoreCard
          onSelectSymbol={setSelectedSymbol}
          selectedSymbol={selectedSymbol}
        />
        <ScreenerHistoryCard />
      </section>
    </DashboardShell>
  );
}
