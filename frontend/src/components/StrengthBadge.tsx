"use client";

// Screener Strength Score card (Phase 3 Day 15).
// Skor kekuatan lintas-strategi 0-100 dari GET /api/strength/{ticker} + daftar
// strategi yang lolos beserta bobotnya.

import { getStrength } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function strengthTone(strength: number): { ring: string; text: string; label: string } {
  if (strength >= 75) return { ring: "text-emerald-400", text: "text-emerald-200", label: "Sangat kuat" };
  if (strength >= 50) return { ring: "text-sky-400", text: "text-sky-200", label: "Kuat" };
  if (strength >= 25) return { ring: "text-amber-400", text: "text-amber-200", label: "Moderat" };
  return { ring: "text-slate-500", text: "text-slate-300", label: "Lemah" };
}

function StrengthRing({ strength }: { strength: number }) {
  const tone = strengthTone(strength);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const filled = (strength / 100) * circumference;

  return (
    <div className="relative h-28 w-28">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
        <circle
          className="text-white/[0.07]"
          cx="50"
          cy="50"
          fill="none"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
        />
        <circle
          className={tone.ring}
          cx="50"
          cy="50"
          fill="none"
          r={radius}
          stroke="currentColor"
          strokeDasharray={`${filled} ${circumference - filled}`}
          strokeLinecap="round"
          strokeWidth="8"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-2xl font-bold tabular-nums ${tone.text}`}>{strength}</span>
        <span className="text-[10px] text-slate-500">/ 100</span>
      </div>
    </div>
  );
}

export function StrengthBadge({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getStrength(symbol), [symbol]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Strength Score</h2>
        <div className="flex items-center gap-2">
          {data && <CachedBadge cached={data.cached} />}
          <span className="text-xs font-medium text-slate-400">{data?.ticker ?? symbol}</span>
        </div>
      </div>
      <p className="mb-4 text-xs text-slate-500">Kekuatan lintas 9 strategi screening</p>

      {status === "loading" && <CardSkeleton lines={5} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="flex items-center gap-5">
          <StrengthRing strength={data.strength} />
          <div className="min-w-0 flex-1">
            <p className={`text-sm font-semibold ${strengthTone(data.strength).text}`}>
              {strengthTone(data.strength).label}
            </p>
            {data.breakdown.length === 0 ? (
              <p className="mt-1 text-xs text-slate-500">
                Tidak lolos strategi apa pun hari ini.
              </p>
            ) : (
              <ul className="mt-2 space-y-1">
                {data.breakdown.map((component) => (
                  <li
                    className="flex items-center justify-between gap-2 text-xs"
                    key={component.strategy}
                  >
                    <span
                      className={
                        component.type === "fundamental" ? "text-amber-200" : "text-sky-200"
                      }
                    >
                      {component.strategy}
                    </span>
                    <span className="tabular-nums text-slate-400">
                      +{component.weight.toFixed(1)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-2 text-[11px] text-slate-500">
              {data.points.toFixed(1)} / {data.max_points.toFixed(0)} poin berbobot
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
