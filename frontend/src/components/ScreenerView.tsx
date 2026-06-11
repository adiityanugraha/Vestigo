"use client";

import { useState } from "react";
import { AiReportCard } from "./AiReportCard";
import { CandlestickChart } from "./CandlestickChart";
import { CompositeScoreCard } from "./CompositeScoreCard";
import { DashboardShell } from "./DashboardShell";
import { ExplainPanel } from "./ExplainPanel";
import { ForecastCard } from "./ForecastCard";
import { MarketBreadthCard } from "./MarketBreadthCard";
import { PredictionPanel } from "./PredictionPanel";
import { RiskMeterCard } from "./RiskMeterCard";
import { ScreenerHistoryCard } from "./ScreenerHistoryCard";
import { StrengthBadge } from "./StrengthBadge";
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

      {/* Phase 3 (Day 15): forecast multi-horizon, strength lintas-strategi,
          dan panel penjelasan untuk saham terpilih */}
      <section className="grid gap-6 lg:grid-cols-2">
        <ForecastCard symbol={selectedSymbol} />
        <StrengthBadge symbol={selectedSymbol} />
      </section>

      <ExplainPanel symbol={selectedSymbol} />

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
