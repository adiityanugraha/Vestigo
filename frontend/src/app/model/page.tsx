import { DashboardShell } from "@/components/DashboardShell";
import { SignalDashboard } from "@/components/tsfm/SignalDashboard";
import { ModelTabs, ResearchStatus } from "@/components/tsfm/shared";

export default function Page() {
  return (
    <DashboardShell activeNav="Model" eyebrow="Vestigo-TSFM · alat riset, bukan sinyal beli" title="Peringkat harian">
      <ModelTabs />
      <ResearchStatus />
      <SignalDashboard />
    </DashboardShell>
  );
}
