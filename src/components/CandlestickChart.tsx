const candles = [
  { height: "42%", wick: "60%", color: "bg-emerald-400" },
  { height: "64%", wick: "78%", color: "bg-emerald-400" },
  { height: "36%", wick: "58%", color: "bg-rose-400" },
  { height: "72%", wick: "88%", color: "bg-emerald-400" },
  { height: "54%", wick: "70%", color: "bg-rose-400" },
  { height: "82%", wick: "92%", color: "bg-emerald-400" },
  { height: "68%", wick: "80%", color: "bg-emerald-400" },
];

export function CandlestickChart() {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-base font-semibold text-white">Candlestick</h2>
        <span className="text-xs font-medium text-slate-400">Daily OHLCV</span>
      </div>
      <div className="flex h-72 items-end gap-4 border-b border-l border-white/10 px-4 pb-4">
        {candles.map((candle, index) => (
          <div
            className="flex h-full flex-1 items-end justify-center"
            key={`${candle.height}-${index}`}
          >
            <div
              className="relative flex w-full max-w-8 items-end justify-center"
              style={{ height: candle.wick }}
            >
              <span className="absolute h-full w-px bg-slate-500" />
              <span
                className={`relative z-10 w-full rounded-sm ${candle.color}`}
                style={{ height: candle.height }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
