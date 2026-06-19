"use client";

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type CandlestickData,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { getMarketData } from "@/lib/api";
import { fmtPrice, fmtPct } from "@/lib/format";
import { useMode } from "./ModeProvider";

type CandlestickChartProps = {
  symbol: string;
};

type ChartState =
  | { status: "loading"; error: null; last: null }
  | { status: "ready"; error: null; last: { price: number; change: number } | null }
  | { status: "error"; error: string; last: null };

export function CandlestickChart({ symbol }: CandlestickChartProps) {
  const { pro } = useMode();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [state, setState] = useState<ChartState>({
    status: "loading",
    error: null,
    last: null,
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        horzLines: { color: "rgba(255, 255, 255, 0.05)" },
        vertLines: { color: "rgba(255, 255, 255, 0.04)" },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "rgba(255, 255, 255, 0.08)" },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.08)",
        timeVisible: true,
      },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      borderUpColor: "#22c55e",
      wickUpColor: "#4ade80",
      downColor: "#ef4444",
      borderDownColor: "#ef4444",
      wickDownColor: "#f87171",
    });
    let ignore = false;

    chartRef.current = chart;
    setState({ status: "loading", error: null, last: null });

    getMarketData(symbol)
      .then((response) => {
        if (ignore) return;

        const chartData: CandlestickData[] = response.bars
          .filter(
            (bar) =>
              bar.open !== null &&
              bar.high !== null &&
              bar.low !== null &&
              bar.close !== null,
          )
          .map((bar) => ({
            time: toUtcTimestamp(bar.date),
            open: bar.open as number,
            high: bar.high as number,
            low: bar.low as number,
            close: bar.close as number,
          }));

        series.setData(chartData);
        chart.timeScale().fitContent();

        const n = chartData.length;
        const last =
          n >= 2
            ? {
                price: chartData[n - 1].close,
                change:
                  ((chartData[n - 1].close - chartData[n - 2].close) /
                    chartData[n - 2].close) *
                  100,
              }
            : n === 1
              ? { price: chartData[0].close, change: 0 }
              : null;

        setState({ status: "ready", error: null, last });
      })
      .catch((error: unknown) => {
        if (ignore) return;
        setState({
          status: "error",
          error: error instanceof Error ? error.message : "Gagal memuat data chart",
          last: null,
        });
      });

    return () => {
      ignore = true;
      chart.remove();
      chartRef.current = null;
    };
  }, [symbol]);

  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h2 className="card-title">{symbol} · Candlestick</h2>
          <p className="card-sub mono">
            {pro ? "Daily OHLCV · 60 sesi terakhir" : "60 sesi terakhir"}
          </p>
        </div>
        <div className="chart-ctrls">
          {pro ? (
            <>
              <button className="ghost-btn ghost-on">Daily OHLCV</button>
              <button className="ghost-btn">MA</button>
              <button className="ghost-btn">Volume</button>
            </>
          ) : (
            <button className="ghost-btn ghost-on">Daily</button>
          )}
        </div>
      </div>

      {state.status === "ready" && state.last && (
        <div className="price-strip">
          <span className="price-big mono">{fmtPrice(state.last.price)}</span>
          <span
            className={`price-chg mono ${
              state.last.change > 0 ? "num-up" : state.last.change < 0 ? "num-down" : ""
            }`}
          >
            {fmtPct(state.last.change)}
          </span>
        </div>
      )}

      <div
        className="relative overflow-hidden"
        style={{
          height: pro ? 320 : 280,
          borderRadius: "var(--r-tile)",
          background: "var(--s2)",
        }}
      >
        <div className="absolute inset-0" ref={containerRef} />

        {state.status === "loading" && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div style={{ width: 208 }}>
              <p className="ta-c small t2">Memuat chart…</p>
              <div className="riskbar mt">
                <div
                  className="riskbar-fill"
                  style={{ width: "66%", background: "var(--accent)" }}
                />
              </div>
            </div>
          </div>
        )}

        {state.status === "error" && (
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <div className="empty-state">
              <p style={{ color: "var(--down)", fontWeight: 500 }}>Gagal memuat chart.</p>
              <p className="small mt">{state.error}</p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function toUtcTimestamp(date: string): UTCTimestamp {
  return Math.floor(new Date(`${date}T00:00:00Z`).getTime() / 1000) as UTCTimestamp;
}
