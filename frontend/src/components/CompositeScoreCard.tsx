"use client";

import { getRanking } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function scoreTone(score: number): string {
  if (score >= 65) return "text-emerald-300";
  if (score >= 45) return "text-amber-300";
  return "text-rose-300";
}

export function CompositeScoreCard({
  onSelectSymbol,
  selectedSymbol,
}: {
  onSelectSymbol: (symbol: string) => void;
  selectedSymbol: string;
}) {
  const { status, data, error, reload } = useApi(() => getRanking(15, true), []);

  return (
    <section className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-white">Composite Score</h2>
          <p className="mt-0.5 text-xs text-slate-500">Ranking Overall Score 0–100</p>
        </div>
        {data && <CachedBadge cached={data.cached} />}
      </div>

      <div className="p-5">
        {status === "loading" && <CardSkeleton lines={6} />}
        {status === "error" && <CardError message={error} onRetry={reload} />}
        {status === "ready" && data && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-400">
                <tr>
                  <th className="py-2 pr-3 font-medium">#</th>
                  <th className="py-2 pr-3 font-medium">Symbol</th>
                  <th className="py-2 pr-3 text-right font-medium">Score</th>
                  <th className="hidden py-2 pr-3 text-right font-medium sm:table-cell">Tech</th>
                  <th className="hidden py-2 pr-3 text-right font-medium sm:table-cell">Mom</th>
                  <th className="hidden py-2 pr-3 text-right font-medium sm:table-cell">ML</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {data.items.map((item) => {
                  const isSelected = item.ticker === selectedSymbol.replace(/\.JK$/i, "");
                  return (
                    <tr
                      key={item.ticker}
                      className={`transition-colors hover:bg-white/[0.04] ${
                        isSelected ? "bg-sky-400/10" : ""
                      }`}
                    >
                      <td className="py-2.5 pr-3 text-slate-500">{item.rank}</td>
                      <td className="py-2.5 pr-3">
                        <button
                          className={`rounded-md px-2 py-1 font-semibold transition-colors ${
                            isSelected
                              ? "bg-sky-400/20 text-sky-100"
                              : "text-white hover:bg-white/10"
                          }`}
                          onClick={() => onSelectSymbol(item.ticker)}
                          type="button"
                        >
                          {item.ticker}
                        </button>
                      </td>
                      <td
                        className={`py-2.5 pr-3 text-right font-bold tabular-nums ${scoreTone(
                          item.overall_score,
                        )}`}
                      >
                        {item.overall_score.toFixed(1)}
                      </td>
                      <td className="hidden py-2.5 pr-3 text-right tabular-nums text-slate-400 sm:table-cell">
                        {item.breakdown.technical.toFixed(0)}
                      </td>
                      <td className="hidden py-2.5 pr-3 text-right tabular-nums text-slate-400 sm:table-cell">
                        {item.breakdown.momentum.toFixed(0)}
                      </td>
                      <td className="hidden py-2.5 pr-3 text-right tabular-nums text-slate-400 sm:table-cell">
                        {item.breakdown.ml === null ? "—" : item.breakdown.ml.toFixed(0)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
