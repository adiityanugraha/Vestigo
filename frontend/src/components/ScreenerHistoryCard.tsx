"use client";

import { getHistory } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CardError, CardSkeleton } from "./CardStatus";

function outcomeTone(outcome: string): string {
  if (outcome === "WIN") return "text-emerald-300";
  if (outcome === "LOSS") return "text-rose-300";
  if (outcome === "PENDING") return "text-slate-500";
  return "text-slate-300";
}

function signed(value: number | null): string {
  if (value === null) return "—";
  const pct = (value * 100).toFixed(2);
  return value > 0 ? `+${pct}%` : `${pct}%`;
}

export function ScreenerHistoryCard() {
  const { status, data, error, reload } = useApi(() => getHistory({ horizon: 7, limit: 30 }), []);

  return (
    <section className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-base font-semibold text-white">Screener History</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Performa {data?.horizon ?? 7} hari setelah lolos screener
          </p>
        </div>
      </div>

      <div className="p-5">
        {status === "loading" && <CardSkeleton lines={6} />}
        {status === "error" && <CardError message={error} onRetry={reload} />}
        {status === "ready" && data && (
          <div className="space-y-4">
            {/* Ringkasan winrate per strategi */}
            <div className="grid grid-cols-2 gap-3">
              {data.summary.map((s) => (
                <div
                  key={s.strategy}
                  className="rounded-lg border border-white/10 bg-slate-950/40 p-3"
                >
                  <p className="text-xs text-slate-500">{s.strategy} winrate</p>
                  <p className="mt-1 text-lg font-bold tabular-nums text-white">
                    {s.winrate === null ? "—" : `${(s.winrate * 100).toFixed(1)}%`}
                  </p>
                  <p className="text-[11px] text-slate-500">
                    {s.wins}W / {s.losses}L dari {s.evaluated}
                  </p>
                </div>
              ))}
              {data.summary.length === 0 && (
                <p className="text-sm text-slate-500">Belum ada data terevaluasi.</p>
              )}
            </div>

            {/* Daftar entri terbaru */}
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="py-2 pr-3 font-medium">Tanggal</th>
                    <th className="py-2 pr-3 font-medium">Symbol</th>
                    <th className="py-2 pr-3 font-medium">Strat</th>
                    <th className="py-2 pr-3 text-right font-medium">Return</th>
                    <th className="py-2 pr-3 text-right font-medium">Hasil</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {data.entries.slice(0, 15).map((e, index) => (
                    <tr key={`${e.date}-${e.ticker}-${e.strategy}-${index}`}>
                      <td className="py-2 pr-3 text-slate-400">{e.date}</td>
                      <td className="py-2 pr-3 font-semibold text-white">{e.ticker}</td>
                      <td className="py-2 pr-3 text-slate-400">{e.strategy}</td>
                      <td className="py-2 pr-3 text-right tabular-nums text-slate-200">
                        {signed(e.forward_return)}
                      </td>
                      <td
                        className={`py-2 pr-3 text-right font-medium ${outcomeTone(e.outcome)}`}
                      >
                        {e.outcome}
                      </td>
                    </tr>
                  ))}
                  {data.entries.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-4 text-slate-500">
                        Belum ada riwayat screener.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
