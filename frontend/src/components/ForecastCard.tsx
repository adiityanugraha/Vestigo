"use client";

// Probability Forecast card (Phase 3 Day 15).
// P(return > 0) untuk 1D / 5D / 20D dari GET /api/forecast/{ticker} + confidence
// level + disclaimer (wajib tampil — alat bantu, bukan rekomendasi).

import { getForecast, type ForecastResponse } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

const HORIZON_LABELS: Array<{ key: keyof ForecastResponse["prob"]; label: string }> = [
  { key: "1d", label: "1 Hari" },
  { key: "5d", label: "5 Hari" },
  { key: "20d", label: "20 Hari" },
];

function confidenceTone(confidence: string): string {
  if (confidence === "HIGH") return "border-emerald-400/30 bg-emerald-500/15 text-emerald-200";
  if (confidence === "MEDIUM") return "border-amber-400/30 bg-amber-500/15 text-amber-200";
  return "border-white/15 bg-white/[0.06] text-slate-300";
}

function probTone(p: number): string {
  if (p >= 0.55) return "bg-emerald-400";
  if (p >= 0.5) return "bg-emerald-400/60";
  if (p >= 0.45) return "bg-amber-400/70";
  return "bg-rose-400/70";
}

function ProbRow({ label, value }: { label: string; value: number }) {
  const pct = value * 100;
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between text-sm">
        <span className="text-slate-300">{label}</span>
        <span className="font-semibold tabular-nums text-slate-100">{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className={`h-full rounded-full ${probTone(value)}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function ForecastCard({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getForecast(symbol), [symbol]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Probability Forecast</h2>
        <div className="flex items-center gap-2">
          {data && <CachedBadge cached={data.cached} />}
          {data && (
            <span
              className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${confidenceTone(data.confidence)}`}
            >
              {data.confidence}
            </span>
          )}
        </div>
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Probabilitas return positif · {data?.ticker ?? symbol}
      </p>

      {status === "loading" && <CardSkeleton lines={5} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-4">
          {HORIZON_LABELS.map(({ key, label }) => (
            <ProbRow key={key} label={label} value={data.prob[key]} />
          ))}
          <p className="border-t border-white/5 pt-3 text-[11px] leading-relaxed text-slate-500">
            {data.disclaimer}
          </p>
        </div>
      )}
    </section>
  );
}
