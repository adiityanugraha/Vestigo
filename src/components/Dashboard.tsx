import { CandlestickChart } from "./CandlestickChart";
import { DashboardShell } from "./DashboardShell";
import { Heatmap } from "./Heatmap";
import { PredictionPanel } from "./PredictionPanel";

export function Dashboard() {
  return (
    <DashboardShell>
      <section className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
        <CandlestickChart />
        <Heatmap />
      </section>

      <PredictionPanel />
    </DashboardShell>
  );
}
