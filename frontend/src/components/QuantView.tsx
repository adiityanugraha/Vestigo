"use client";

// Quant Analytics Dashboard (Phase 4, Pro-only page).

import { DashboardShell } from "./DashboardShell";
import { StrategyBenchmark } from "./quant/StrategyBenchmark";
import { EquityCurveChart } from "./quant/EquityCurveChart";
import { MarketReplay } from "./quant/MarketReplay";
import { MonteCarloChart } from "./quant/MonteCarloChart";
import { RiskExposure } from "./quant/RiskExposure";
import { CorrelationHeatmap } from "./quant/CorrelationHeatmap";
import { PortfolioBuilder } from "./quant/PortfolioBuilder";

export function QuantView() {
  return (
    <DashboardShell activeNav="Quant" eyebrow="Quant Research Platform" title="Quant Analytics">
      <StrategyBenchmark />
      <div className="grid-2">
        <EquityCurveChart />
        <MonteCarloChart />
      </div>
      <RiskExposure />
      <CorrelationHeatmap />
      <MarketReplay />
      <PortfolioBuilder />
    </DashboardShell>
  );
}
