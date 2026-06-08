"use client";

import { AiReportCard } from "./AiReportCard";
import { CandlestickChart } from "./CandlestickChart";
import { DashboardShell } from "./DashboardShell";
import { RiskMeterCard } from "./RiskMeterCard";
import { SupportResistanceCard } from "./SupportResistanceCard";

// Dashboard menampilkan KONTEKS PASAR: IHSG (Indeks Harga Saham Gabungan).
// Simbol dikunci ke IHSG — chart, AI report, risk meter, dan support/resistance.
const IHSG_SYMBOL = "IHSG";

export function Dashboard() {
  return (
    <DashboardShell
      activeNav="Dashboard"
      eyebrow="IDX Market Context"
      title="IHSG · Indeks Harga Saham Gabungan"
    >
      <section className="grid gap-6">
        <CandlestickChart symbol={IHSG_SYMBOL} />
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <AiReportCard symbol={IHSG_SYMBOL} />
        <RiskMeterCard symbol={IHSG_SYMBOL} />
        <SupportResistanceCard symbol={IHSG_SYMBOL} />
      </section>
    </DashboardShell>
  );
}
