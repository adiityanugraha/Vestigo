"use client";

// AI Daily Report (Phase 5 Day 15) — laporan harian + ekspor PDF/Markdown.
// GET /api/daily-report (auto-load); tombol unduh ke endpoint format=pdf|markdown.

import { dailyReportUrl, getDailyReport } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "../CardStatus";

export function DailyReport() {
  const state = useApi(getDailyReport, []);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">AI Daily Report</h2>
        <div className="flex gap-2">
          <a
            href={dailyReportUrl("markdown")}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-white/10 px-3 py-1 text-xs text-slate-300 transition-colors hover:bg-white/5"
          >
            Markdown
          </a>
          <a
            href={dailyReportUrl("pdf")}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-sky-400/40 bg-sky-500/15 px-3 py-1 text-xs font-medium text-sky-100 transition-colors hover:bg-sky-500/25"
          >
            Unduh PDF
          </a>
        </div>
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Top Opportunities, sektor, high-confidence, dan peringatan risiko.
      </p>

      {state.status === "loading" && <CardSkeleton lines={6} />}
      {state.status === "error" && <CardError message={state.error} onRetry={state.reload} />}
      {state.status === "ready" && (
        <div className="space-y-4 text-sm">
          {state.data.date && <p className="text-xs text-slate-500">{state.data.date}</p>}
          {state.data.overview && <p className="text-slate-200">{state.data.overview}</p>}

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                Top Opportunities
              </p>
              <ul className="space-y-1">
                {state.data.top_opportunities.map((o) => (
                  <li key={o.ticker} className="flex justify-between text-slate-300">
                    <span className="font-medium text-white">{o.ticker}</span>
                    <span className="tabular-nums text-sky-200">{o.overall_score}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
                High Confidence
              </p>
              {state.data.high_confidence.length > 0 ? (
                <ul className="space-y-1">
                  {state.data.high_confidence.map((h) => (
                    <li key={h.ticker} className="flex justify-between text-slate-300">
                      <span className="font-medium text-white">{h.ticker}</span>
                      <span className="tabular-nums text-emerald-300">
                        {h.prob_5d != null ? `${(h.prob_5d * 100).toFixed(0)}%` : "-"}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">Tidak ada.</p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-400">
            <span>
              Sektor terkuat:{" "}
              <span className="font-semibold text-emerald-300">{state.data.strongest_sector ?? "-"}</span>
            </span>
            <span>
              Sektor terlemah:{" "}
              <span className="font-semibold text-rose-300">{state.data.weakest_sector ?? "-"}</span>
            </span>
          </div>

          {state.data.risk_warnings.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-rose-300">
                Risk Warning
              </p>
              <ul className="space-y-1">
                {state.data.risk_warnings.map((w) => (
                  <li key={w.ticker} className="text-slate-300">
                    {w.ticker}: risiko {w.risk} (skor {w.score ?? "-"})
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[11px] leading-relaxed text-slate-500">{state.data.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
