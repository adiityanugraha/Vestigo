import { BacktestPanel } from "@/components/BacktestPanel";
import { DashboardShell } from "@/components/DashboardShell";

export default function BacktestPage() {
  return (
    <DashboardShell
      activeNav="Backtest"
      eyebrow="Strategy Evaluation"
      title="Backtesting"
    >
      <BacktestPanel />
    </DashboardShell>
  );
}
