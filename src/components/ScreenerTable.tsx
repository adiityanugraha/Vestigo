import type { PredictedScreenerCandidate } from "@/lib/predictionPipeline";

type ScreenerTableProps = {
  isLoading?: boolean;
  title: string;
  rows: PredictedScreenerCandidate[];
};

export function ScreenerTable({
  isLoading = false,
  title,
  rows,
}: ScreenerTableProps) {
  return (
    <section className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
      <div className="border-b border-white/10 px-5 py-4">
        <h2 className="text-base font-semibold text-white">{title}</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/[0.04] text-xs uppercase text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Symbol</th>
              <th className="px-5 py-3 font-medium">Prob</th>
              <th className="px-5 py-3 font-medium">Entry</th>
              <th className="px-5 py-3 font-medium">SL</th>
              <th className="px-5 py-3 font-medium">TP</th>
              <th className="px-5 py-3 font-medium">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {isLoading &&
              Array.from({ length: 3 }, (_, index) => (
                <tr className="text-slate-300" key={index}>
                  {Array.from({ length: 6 }, (_, cellIndex) => (
                    <td className="px-5 py-4" key={cellIndex}>
                      <div className="h-3 w-20 animate-pulse rounded-full bg-white/10" />
                    </td>
                  ))}
                </tr>
              ))}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td className="px-5 py-5 text-slate-400" colSpan={6}>
                  No candidates match the current strict strategy filters.
                </td>
              </tr>
            )}
            {!isLoading && rows.map((row) => (
              <tr
                className="text-slate-200"
                key={`${row.current.symbol}-${row.strategy}`}
              >
                <td className="px-5 py-4 font-semibold text-white">
                  {row.current.symbol}
                </td>
                <td className="px-5 py-4 text-emerald-300">
                  {(row.prediction.probabilityUp * 100).toFixed(1)}%
                </td>
                <td className="px-5 py-4">{formatPrice(row.levels.entry)}</td>
                <td className="px-5 py-4">{formatPrice(row.levels.stopLoss)}</td>
                <td className="px-5 py-4">{formatPrice(row.levels.takeProfit)}</td>
                <td className="px-5 py-4">{formatCompact(row.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function formatPrice(value: number): string {
  return value.toLocaleString("id-ID", { maximumFractionDigits: 0 });
}

function formatCompact(value: number): string {
  return Intl.NumberFormat("id-ID", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}
