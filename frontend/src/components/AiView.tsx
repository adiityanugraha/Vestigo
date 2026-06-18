"use client";

// AI Analyst Dashboard (Phase 5 Day 15).
// Menyusun seluruh card lapisan AI di halaman /ai.

import { DashboardShell } from "./DashboardShell";
import { MarketNarrator } from "./ai/MarketNarrator";
import { DailyReport } from "./ai/DailyReport";
import { ChatWithStock } from "./ai/ChatWithStock";
import { AIAnalysis } from "./ai/AIAnalysis";
import { ExplainScore } from "./ai/ExplainScore";
import { StrategyComparator } from "./ai/StrategyComparator";
import { PortfolioAdvisor } from "./ai/PortfolioAdvisor";

export function AiView() {
  return (
    <DashboardShell activeNav="AI" eyebrow="AI Financial Analyst" title="AI Analyst">
      <MarketNarrator />
      <DailyReport />
      <ChatWithStock />
      <div className="grid gap-6 lg:grid-cols-2">
        <AIAnalysis />
        <ExplainScore />
      </div>
      <StrategyComparator />
      <PortfolioAdvisor />
    </DashboardShell>
  );
}
