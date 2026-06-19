"use client";

// AI Analyst (Phase 5).
// Lite = Market Narrator + AI Daily Report + Chat With Stock.
// Pro  = + AI Analyst per-saham, Explainable AI 2.0, Strategy Comparator, Portfolio Advisor.

import { DashboardShell } from "./DashboardShell";
import { useMode } from "./ModeProvider";
import { MarketNarrator } from "./ai/MarketNarrator";
import { DailyReport } from "./ai/DailyReport";
import { ChatWithStock } from "./ai/ChatWithStock";
import { AIAnalysis } from "./ai/AIAnalysis";
import { ExplainScore } from "./ai/ExplainScore";
import { StrategyComparator } from "./ai/StrategyComparator";
import { PortfolioAdvisor } from "./ai/PortfolioAdvisor";

export function AiView() {
  const { pro } = useMode();

  return (
    <DashboardShell activeNav="AI" eyebrow="AI Financial Analyst" title="AI Analyst">
      <MarketNarrator />
      <DailyReport />
      <ChatWithStock />

      {pro && (
        <>
          <div className="grid-2">
            <AIAnalysis />
            <ExplainScore />
          </div>
          <StrategyComparator />
          <PortfolioAdvisor />
        </>
      )}
    </DashboardShell>
  );
}
