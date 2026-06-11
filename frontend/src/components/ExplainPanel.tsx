"use client";

// Explainable AI + Explain Why Selected (Phase 3 Day 15).
// Kiri : /api/explain — confidence + bullish factors + risk factors.
// Kanan: /api/why — strategi yang cocok + alasan spesifik per kriteria yang
//        benar-benar lolos (termasuk catatan kriteria yang dilewati karena
//        keterbatasan data).

import { getExplain, getWhy } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { CachedBadge, CardError, CardSkeleton } from "./CardStatus";

function FactorList({
  factors,
  tone,
  sign,
  emptyText,
}: {
  factors: string[];
  tone: string;
  sign: string;
  emptyText: string;
}) {
  if (factors.length === 0) {
    return <p className="text-xs text-slate-500">{emptyText}</p>;
  }
  return (
    <ul className="space-y-1.5">
      {factors.map((factor) => (
        <li className="flex gap-2 text-xs text-slate-300" key={factor}>
          <span className={`shrink-0 font-bold ${tone}`}>{sign}</span>
          <span>{factor}</span>
        </li>
      ))}
    </ul>
  );
}

function ExplainSide({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getExplain(symbol), [symbol]);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-white">Explainable AI</h3>
        <div className="flex items-center gap-2">
          {data && <CachedBadge cached={data.cached} />}
          {data && (
            <span className="rounded-md border border-sky-300/30 bg-sky-500/15 px-2 py-0.5 text-[11px] font-semibold text-sky-200">
              Confidence {data.confidence}%
            </span>
          )}
        </div>
      </div>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-4">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-300/80">
              Bullish factors
            </p>
            <FactorList
              emptyText="Tidak ada sinyal bullish menonjol."
              factors={data.bullish_factors}
              sign="+"
              tone="text-emerald-300"
            />
          </div>
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-rose-300/80">
              Risk factors
            </p>
            <FactorList
              emptyText="Tidak ada sinyal risiko menonjol."
              factors={data.risk_factors}
              sign="−"
              tone="text-rose-300"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function WhySide({ symbol }: { symbol: string }) {
  const { status, data, error, reload } = useApi(() => getWhy(symbol), [symbol]);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-white">Why Selected</h3>
        {data && data.matched.length > 0 && (
          <span className="rounded-md border border-emerald-300/30 bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-200">
            {data.matched.length} strategi cocok
          </span>
        )}
      </div>

      {status === "loading" && <CardSkeleton lines={6} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <div className="space-y-3">
          {data.matched_strategies.length === 0 ? (
            <p className="text-xs text-slate-500">
              Saham ini tidak lolos strategi screening mana pun hari ini.
            </p>
          ) : (
            data.matched_strategies.map((strategy) => (
              <article
                className="rounded-lg border border-white/10 bg-white/[0.02] p-3"
                key={strategy.key}
              >
                <p className="mb-2 text-sm font-semibold text-slate-100">
                  <span className="mr-2 text-emerald-300">V</span>
                  {strategy.name}
                  <span
                    className={`ml-2 rounded px-1.5 py-0.5 text-[10px] font-medium ${
                      strategy.type === "fundamental"
                        ? "bg-amber-500/15 text-amber-200"
                        : "bg-sky-500/15 text-sky-200"
                    }`}
                  >
                    {strategy.type}
                  </span>
                </p>
                <FactorList
                  emptyText="—"
                  factors={strategy.reasons}
                  sign="+"
                  tone="text-emerald-300"
                />
                {strategy.skipped.length > 0 && (
                  <p className="mt-2 text-[11px] italic text-slate-500">
                    {strategy.skipped.length} kriteria dilewati (data tidak tersedia di
                    sumber gratis)
                  </p>
                )}
              </article>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export function ExplainPanel({ symbol }: { symbol: string }) {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">Explain · {symbol}</h2>
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Kenapa saham ini terpilih — penjelasan dari kriteria yang benar-benar lolos
      </p>
      <div className="grid gap-6 lg:grid-cols-2">
        <ExplainSide symbol={symbol} />
        <WhySide symbol={symbol} />
      </div>
    </section>
  );
}
