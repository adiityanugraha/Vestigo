"use client";

// Correlation Heatmap (Phase 4 Day 15).
// Matriks korelasi return harian (universe LQ45) dari GET /api/correlation.
// Sel diwarnai: merah = korelasi positif tinggi, biru = negatif.

import { getCorrelation } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "../CardStatus";

function cellColor(corr: number): string {
  // corr dalam [-1,1]. Positif -> merah, negatif -> biru, intensitas = |corr|.
  const a = Math.min(Math.abs(corr), 1);
  return corr >= 0
    ? `rgba(244, 63, 94, ${a * 0.85})`
    : `rgba(56, 189, 248, ${a * 0.85})`;
}

export function CorrelationHeatmap() {
  const { status, data, error, reload } = useApi(() => getCorrelation("lq45", 90), []);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Correlation Matrix</h2>
        {data && <CachedBadge cached={data.cached} />}
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Korelasi return harian LQ45 (90 hari) — bantu diversifikasi. Merah = bergerak
        seragam, biru = berlawanan.
      </p>

      {status === "loading" && <CardSkeleton lines={8} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <>
          <div className="overflow-auto">
            <table className="border-separate border-spacing-0 text-[9px]">
              <thead>
                <tr>
                  <th className="sticky left-0 z-10 bg-[#0a0f1e] p-1" />
                  {data.tickers.map((t) => (
                    <th
                      key={t}
                      className="h-16 w-5 p-0 align-bottom font-normal text-slate-500"
                    >
                      <span className="inline-block origin-bottom-left translate-y-1 rotate-[-60deg] whitespace-nowrap">
                        {t}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.tickers.map((rowTicker, i) => (
                  <tr key={rowTicker}>
                    <th className="sticky left-0 z-10 bg-[#0a0f1e] pr-2 text-right font-medium text-slate-400">
                      {rowTicker}
                    </th>
                    {data.matrix[i].map((corr, j) => (
                      <td
                        key={j}
                        className="h-5 w-5 border border-[#0a0f1e]"
                        style={{ backgroundColor: cellColor(corr) }}
                        title={`${rowTicker} vs ${data.tickers[j]}: ${corr.toFixed(2)}`}
                      />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4">
            <p className="mb-2 text-xs font-medium text-slate-400">
              Pasangan paling berkorelasi (waspadai konsentrasi):
            </p>
            <div className="flex flex-wrap gap-2">
              {data.top_correlated.slice(0, 8).map((p) => (
                <span
                  key={`${p.ticker_a}-${p.ticker_b}`}
                  className="rounded-md border border-rose-400/20 bg-rose-500/10 px-2 py-0.5 text-[11px] text-rose-200"
                >
                  {p.ticker_a}-{p.ticker_b} {p.correlation.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{data.disclaimer}</p>
        </>
      )}
    </section>
  );
}
