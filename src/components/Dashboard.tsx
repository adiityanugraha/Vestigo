"use client";

import { useState } from "react";
import { CandlestickChart } from "./CandlestickChart";
import { DashboardShell } from "./DashboardShell";
import { Heatmap } from "./Heatmap";
import { PredictionPanel } from "./PredictionPanel";

export function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState("BBCA.JK");

  return (
    <DashboardShell>
      <section className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
        <CandlestickChart symbol={selectedSymbol} />
        <Heatmap />
      </section>

      <PredictionPanel
        onSelectSymbol={setSelectedSymbol}
        selectedSymbol={selectedSymbol}
      />
    </DashboardShell>
  );
}
