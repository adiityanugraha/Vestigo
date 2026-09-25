import { DashboardShell } from "@/components/DashboardShell";
import { TrainingViewer } from "@/components/tsfm/TrainingViewer";
import { ModelTabs, ResearchStatus } from "@/components/tsfm/shared";

export default function Page() {
  return (
    <DashboardShell activeNav="Model" eyebrow="Vestigo-TSFM · alat riset, bukan sinyal beli" title="Training run">
      <ModelTabs />
      <ResearchStatus />
      <TrainingViewer />
    </DashboardShell>
  );
}
