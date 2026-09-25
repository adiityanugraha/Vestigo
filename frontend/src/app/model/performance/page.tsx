import { DashboardShell } from "@/components/DashboardShell";
import { ModelPerformance } from "@/components/tsfm/ModelPerformance";
import { ModelTabs, ResearchStatus } from "@/components/tsfm/shared";

export default function Page() {
  return (
    <DashboardShell activeNav="Model" eyebrow="Vestigo-TSFM · alat riset, bukan sinyal beli" title="Performa model">
      <ModelTabs />
      <ResearchStatus />
      <ModelPerformance />
    </DashboardShell>
  );
}
