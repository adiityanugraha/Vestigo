"use client";

// Quant Analytics Dashboard (Phase 4 Day 14-15).
// Menyusun seluruh card validasi kuantitatif di halaman /quant.

import { DashboardShell } from "./DashboardShell";
import { StrategyBenchmark } from "./quant/StrategyBenchmark";
import { EquityCurveChart } from "./quant/EquityCurveChart";
import { MarketReplay } from "./quant/MarketReplay";

export function QuantView() {
  return (
    <DashboardShell
      activeNav="Quant"
      eyebrow="Quant Research Platform"
      title="Quant Analytics"
    >
      <StrategyBenchmark />
      <EquityCurveChart />
      <MarketReplay />
    </DashboardShell>
  );
}
