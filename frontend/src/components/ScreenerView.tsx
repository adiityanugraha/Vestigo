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

// Page Screener: seluruh analitik per-saham & pasar (dipindah dari dashboard).
// Klik saham di tabel screener / composite score -> card AI/Risk/S&R mengikuti.
export function ScreenerView() {
  const [selectedSymbol, setSelectedSymbol] = useState("BBCA");

  return (
    <DashboardShell
      activeNav="Screener"
      eyebrow="IDX Daily Screener"
      title="Screener"
    >
      <MarketBreadthCard />

      <PredictionPanel
        onSelectSymbol={setSelectedSymbol}
        selectedSymbol={selectedSymbol}
      />

      {/* Analisis saham terpilih dari tabel di atas */}
      <section className="grid gap-6">
        <CandlestickChart symbol={selectedSymbol} />
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <AiReportCard symbol={selectedSymbol} />
        <RiskMeterCard symbol={selectedSymbol} />
        <SupportResistanceCard symbol={selectedSymbol} />
      </section>

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
