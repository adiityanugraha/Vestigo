import { DashboardShell } from "@/components/DashboardShell";
import { BacktestExplorer } from "@/components/tsfm/BacktestExplorer";
import { ModelTabs, ResearchStatus } from "@/components/tsfm/shared";

export default function Page() {
  return (
    <DashboardShell activeNav="Model" eyebrow="Vestigo-TSFM · alat riset, bukan sinyal beli" title="Backtest explorer">
      <ModelTabs />
      <ResearchStatus />
      <BacktestExplorer />
    </DashboardShell>
  );
}
