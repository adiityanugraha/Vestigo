"use client";

import { getStockReport } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function sentimentTone(sentiment: string): string {
  if (sentiment === "Bullish") return "text-emerald-300 border-emerald-400/30 bg-emerald-500/10";
  if (sentiment === "Bearish") return "text-rose-300 border-rose-400/30 bg-rose-500/10";
  return "text-slate-300 border-white/10 bg-white/[0.04]";
}

export function AiReportCard({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getStockReport(symbol), [symbol]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white">AI Stock Report</h2>
          <p className="mt-1 text-xs text-slate-500">{symbol}</p>
        </div>
        {data && <CachedBadge cached={data.cached} />}
      </div>

      {status === "loading" && <CardSkeleton lines={5} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3">
            <span
              className={`rounded-md border px-2.5 py-1 text-sm font-semibold ${sentimentTone(
                data.sentiment,
              )}`}
            >
              {data.sentiment}
            </span>
            <div className="text-right">
              <p className="text-xs text-slate-500">AI Confidence</p>
              <p className="text-2xl font-bold tabular-nums text-white">{data.score}%</p>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-slate-300">{data.summary}</p>

          {data.bullishFactors.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-300">
                Faktor Bullish
              </p>
              <ul className="space-y-1 text-sm text-slate-300">
                {data.bullishFactors.map((factor) => (
                  <li key={factor} className="flex gap-2">
                    <span className="text-emerald-400">+</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.riskFactors.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-rose-300">
                Faktor Risiko
              </p>
              <ul className="space-y-1 text-sm text-slate-300">
                {data.riskFactors.map((factor) => (
                  <li key={factor} className="flex gap-2">
                    <span className="text-rose-400">!</span>
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
