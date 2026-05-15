import { CandlestickChart } from "./CandlestickChart";
import { Heatmap } from "./Heatmap";
import { MarketDataStatus } from "./MarketDataStatus";
import { ScreenerTable } from "./ScreenerTable";

const metrics = [
  { label: "BSJP", value: "Top 5", tone: "text-emerald-300" },
  { label: "BPJS", value: "Top 5", tone: "text-sky-300" },
  { label: "Timeframe", value: "Daily", tone: "text-amber-300" },
];

export function Dashboard() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col justify-between gap-4 border-b border-white/10 pb-6 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-slate-400">
              Pocket Screener
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-normal text-white md:text-4xl">
              IDX Daily Screener
            </h1>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {metrics.map((metric) => (
              <div
                className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-3"
                key={metric.label}
              >
                <p className="text-xs text-slate-400">{metric.label}</p>
                <p className={`mt-1 text-lg font-semibold ${metric.tone}`}>
                  {metric.value}
                </p>
              </div>
            ))}
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <CandlestickChart />
          <Heatmap />
        </section>

        <MarketDataStatus />
        <ScreenerTable />
      </div>
    </main>
  );
}
