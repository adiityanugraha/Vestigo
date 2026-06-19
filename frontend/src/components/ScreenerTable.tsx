"use client";

import { useMemo, useState } from "react";
import { fmtInt, fmtScore, fmtValue } from "@/lib/format";
import { VCard } from "./vestigo/Card";

// Baris screener sederhana (dipetakan dari respons /api/screener backend).
export type ScreenerRow = {
  symbol: string;
  strategy: string;
  probabilityUp: number;
  entry: number;
  stopLoss: number;
  takeProfit: number;
  exit: number;
  value: number;
};

type ScreenerTableProps = {
  isLoading?: boolean;
  onSelectSymbol: (symbol: string) => void;
  title: string;
  rows: ScreenerRow[];
  selectedSymbol: string;
};

type SortDirection = "asc" | "desc";
type SortKey =
  | "symbol"
  | "probabilityUp"
  | "entry"
  | "stopLoss"
  | "takeProfit"
  | "exit"
  | "value";

type SortState = { direction: SortDirection; key: SortKey };

const columns: Array<{ key: SortKey; label: string; num?: boolean }> = [
  { key: "symbol", label: "Symbol" },
  { key: "probabilityUp", label: "Prob", num: true },
  { key: "entry", label: "Entry", num: true },
  { key: "stopLoss", label: "SL", num: true },
  { key: "takeProfit", label: "TP", num: true },
  { key: "exit", label: "Exit", num: true },
  { key: "value", label: "Value", num: true },
];

export function ScreenerTable({
  isLoading = false,
  onSelectSymbol,
  selectedSymbol,
  title,
  rows,
}: ScreenerTableProps) {
  const [sort, setSort] = useState<SortState>({ direction: "desc", key: "probabilityUp" });
  const sortedRows = useMemo(
    () => [...rows].sort((a, b) => compareRows(a, b, sort)),
    [rows, sort],
  );

  function updateSort(key: SortKey) {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "desc" ? "asc" : "desc",
    }));
  }

  const selectedBare = selectedSymbol.replace(/\.JK$/i, "");

  return (
    <VCard title={title} sub="Pick harian · klik header untuk urut" subMono={false}>
      <div className="table-wrap">
        <table className="dtable">
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  aria-sort={getAriaSort(column.key, sort)}
                  className={column.num ? "ta-r" : ""}
                >
                  <button
                    type="button"
                    onClick={() => updateSort(column.key)}
                    className="mono"
                    style={{ font: "inherit", color: "inherit", textTransform: "inherit" }}
                  >
                    {column.label}
                    {sort.key === column.key && (sort.direction === "desc" ? " ↓" : " ↑")}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading &&
              Array.from({ length: 3 }, (_, index) => (
                <tr key={index}>
                  {columns.map((_, cellIndex) => (
                    <td key={cellIndex}>
                      <div className="skel-line" style={{ width: 64 }} />
                    </td>
                  ))}
                </tr>
              ))}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td className="t3" colSpan={columns.length}>
                  Tidak ada kandidat yang lolos filter strategi hari ini.
                </td>
              </tr>
            )}
            {!isLoading &&
              sortedRows.map((row) => {
                const sel = row.symbol === selectedBare;
                return (
                  <tr
                    key={`${row.symbol}-${row.strategy}`}
                    className={sel ? "row-sel" : "row-click"}
                    onClick={() => onSelectSymbol(row.symbol)}
                  >
                    <td>
                      <span className={`tk-pill ${sel ? "tk-sel" : ""}`}>{row.symbol}</span>
                    </td>
                    <td className="ta-r mono num-up">{fmtScore(row.probabilityUp * 100, 1)}%</td>
                    <td className="ta-r mono">{fmtInt(row.entry)}</td>
                    <td className="ta-r mono num-down">{fmtInt(row.stopLoss)}</td>
                    <td className="ta-r mono num-up">{fmtInt(row.takeProfit)}</td>
                    <td className="ta-r mono">{fmtInt(row.exit)}</td>
                    <td className="ta-r mono t2">{fmtValue(row.value)}</td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </VCard>
  );
}

function compareRows(a: ScreenerRow, b: ScreenerRow, sort: SortState): number {
  const first = a[sort.key];
  const second = b[sort.key];
  const multiplier = sort.direction === "asc" ? 1 : -1;
  if (typeof first === "string" && typeof second === "string") {
    return first.localeCompare(second) * multiplier;
  }
  return (Number(first) - Number(second)) * multiplier;
}

function getAriaSort(key: SortKey, sort: SortState) {
  if (key !== sort.key) return "none";
  return sort.direction === "asc" ? "ascending" : "descending";
}
