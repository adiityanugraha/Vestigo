"use client";

import { useMemo, useState } from "react";
import type { PredictedScreenerCandidate } from "@/lib/predictionPipeline";

type ScreenerTableProps = {
  isLoading?: boolean;
  onSelectSymbol: (symbol: string) => void;
  title: string;
  rows: PredictedScreenerCandidate[];
  selectedSymbol: string;
};

type SortDirection = "asc" | "desc";
type SortKey =
  | "symbol"
  | "probability"
  | "entry"
  | "stopLoss"
  | "takeProfit"
  | "exit"
  | "value";

type SortState = {
  direction: SortDirection;
  key: SortKey;
};

const columns: Array<{ key: SortKey; label: string; align?: "right" }> = [
  { key: "symbol", label: "Symbol" },
  { key: "probability", label: "Prob", align: "right" },
  { key: "entry", label: "Entry", align: "right" },
  { key: "stopLoss", label: "SL", align: "right" },
  { key: "takeProfit", label: "TP", align: "right" },
  { key: "exit", label: "Exit", align: "right" },
  { key: "value", label: "Value", align: "right" },
];

export function ScreenerTable({
  isLoading = false,
  onSelectSymbol,
  selectedSymbol,
  title,
  rows,
}: ScreenerTableProps) {
  const [sort, setSort] = useState<SortState>({
    direction: "desc",
    key: "probability",
  });
  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => compareRows(a, b, sort)),
    [rows, sort],
  );

  function updateSort(key: SortKey) {
    setSort((current) => ({
      key,
      direction:
        current.key === key && current.direction === "desc" ? "asc" : "desc",
    }));
  }

  return (
    <section className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.04]">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
        <h2 className="text-base font-semibold text-white">{title}</h2>
        <p className="text-xs text-slate-500">Sortable top 5</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/[0.04] text-xs uppercase text-slate-400">
            <tr>
              {columns.map((column) => (
                <th
                  aria-sort={getAriaSort(column.key, sort)}
                  className={`px-5 py-3 font-medium ${
                    column.align === "right" ? "text-right" : ""
                  }`}
                  key={column.key}
                >
                  <button
                    className={`inline-flex items-center gap-2 transition-colors hover:text-white ${
                      column.align === "right" ? "justify-end" : ""
                    }`}
                    onClick={() => {
                      updateSort(column.key);
                    }}
                    type="button"
                  >
                    {column.label}
                    {sort.key === column.key && (
                      <span className="rounded border border-white/10 px-1.5 py-0.5 text-[10px] normal-case text-slate-300">
                        {sort.direction}
                      </span>
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {isLoading &&
              Array.from({ length: 3 }, (_, index) => (
                <tr className="text-slate-300" key={index}>
                  {Array.from({ length: columns.length }, (_, cellIndex) => (
                    <td className="px-5 py-4" key={cellIndex}>
                      <div className="h-3 w-20 animate-pulse rounded-full bg-white/10" />
                    </td>
                  ))}
                </tr>
              ))}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td className="px-5 py-5 text-slate-400" colSpan={columns.length}>
                  No candidates match the current strict strategy filters.
                </td>
              </tr>
            )}
            {!isLoading &&
              sortedRows.map((row) => {
                const isSelected = row.current.symbol === selectedSymbol;

                return (
                  <tr
                    className={`text-slate-200 transition-colors hover:bg-white/[0.04] ${
                      isSelected ? "bg-sky-400/10" : ""
                    }`}
                    key={`${row.current.symbol}-${row.strategy}`}
                  >
                    <td className="px-5 py-4 font-semibold text-white">
                      <button
                        className={`rounded-md px-2 py-1 text-left transition-colors ${
                          isSelected
                            ? "bg-sky-400/20 text-sky-100"
                            : "text-white hover:bg-white/10"
                        }`}
                        onClick={() => {
                          onSelectSymbol(row.current.symbol);
                        }}
                        type="button"
                      >
                        {row.current.symbol}
                      </button>
                    </td>
                    <td className="px-5 py-4 text-right text-emerald-300">
                      {(row.prediction.probabilityUp * 100).toFixed(1)}%
                    </td>
                    <td className="px-5 py-4 text-right">
                      {formatPrice(row.levels.entry)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {formatPrice(row.levels.stopLoss)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {formatPrice(row.levels.takeProfit)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {formatPrice(row.levels.exit)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      {formatCompact(row.value)}
                    </td>
                  </tr>
                );
              })}
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

function compareRows(
  a: PredictedScreenerCandidate,
  b: PredictedScreenerCandidate,
  sort: SortState,
): number {
  const first = getSortValue(a, sort.key);
  const second = getSortValue(b, sort.key);
  const multiplier = sort.direction === "asc" ? 1 : -1;

  if (typeof first === "string" && typeof second === "string") {
    return first.localeCompare(second) * multiplier;
  }

  return (Number(first) - Number(second)) * multiplier;
}

function getSortValue(
  row: PredictedScreenerCandidate,
  key: SortKey,
): number | string {
  switch (key) {
    case "symbol":
      return row.current.symbol;
    case "probability":
      return row.prediction.probabilityUp;
    case "entry":
      return row.levels.entry;
    case "stopLoss":
      return row.levels.stopLoss;
    case "takeProfit":
      return row.levels.takeProfit;
    case "exit":
      return row.levels.exit;
    case "value":
      return row.value;
  }
}

function getAriaSort(key: SortKey, sort: SortState) {
  if (key !== sort.key) {
    return "none";
  }

  return sort.direction === "asc" ? "ascending" : "descending";
}
