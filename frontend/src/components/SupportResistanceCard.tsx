"use client";

import { getSupportResistance } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function price(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("id-ID", { maximumFractionDigits: 2 });
}

export function SupportResistanceCard({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getSupportResistance(symbol), [symbol]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white">Support &amp; Resistance</h2>
          <p className="mt-1 text-xs text-slate-500">{symbol}</p>
        </div>
        {data && <CachedBadge cached={data.cached} />}
      </div>

      {status === "loading" && <CardSkeleton lines={4} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-3">
          {/* Visual: Resistance di atas, harga di tengah, Support di bawah */}
          <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-4 py-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wide text-rose-300">
                Resistance
              </span>
              <span className="font-semibold tabular-nums text-rose-100">
                {price(data.resistance)}
              </span>
            </div>
          </div>

          <div className="rounded-lg border border-sky-400/30 bg-sky-500/10 px-4 py-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wide text-sky-300">
                Harga saat ini
              </span>
              <span className="font-semibold tabular-nums text-sky-100">
                {price(data.current)}
              </span>
            </div>
          </div>

          <div className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-4 py-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wide text-emerald-300">
                Support
              </span>
              <span className="font-semibold tabular-nums text-emerald-100">
                {price(data.support)}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1 text-sm">
            <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
              <p className="text-xs text-slate-500">Pivot Point</p>
              <p className="mt-1 font-semibold text-slate-100">{price(data.methods.pivot.pivot)}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
              <p className="text-xs text-slate-500">Breakout Zone</p>
              <p className="mt-1 font-semibold text-slate-100">
                {data.breakout_zone
                  ? `${price(data.breakout_zone.lower)} – ${price(data.breakout_zone.upper)}`
                  : "—"}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
