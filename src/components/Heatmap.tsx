const sectors = [
  { name: "Banking", tone: "bg-emerald-500/80" },
  { name: "Energy", tone: "bg-emerald-400/70" },
  { name: "Telco", tone: "bg-sky-500/70" },
  { name: "Consumer", tone: "bg-amber-400/80" },
  { name: "Property", tone: "bg-rose-500/70" },
  { name: "Health", tone: "bg-emerald-300/70" },
];

export function Heatmap() {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-base font-semibold text-white">Market Heatmap</h2>
        <span className="text-xs font-medium text-slate-400">IDX</span>
      </div>
      <div className="grid h-72 grid-cols-2 gap-3">
        {sectors.map((sector) => (
          <div
            className={`flex items-end rounded-lg p-4 ${sector.tone}`}
            key={sector.name}
          >
            <span className="text-sm font-semibold text-slate-950">
              {sector.name}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
