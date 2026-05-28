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
import { fetchDailyOhlcv } from "@/lib/fetchData";

type CandlestickChartProps = {
  symbol: string;
};

type ChartState =
  | { status: "loading"; error: null }
  | { status: "ready"; error: null }
  | { status: "error"; error: string };

export function CandlestickChart({ symbol }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [state, setState] = useState<ChartState>({
    status: "loading",
    error: null,
  });

  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: {
        horzLines: { color: "rgba(148, 163, 184, 0.12)" },
        vertLines: { color: "rgba(148, 163, 184, 0.08)" },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "rgba(148, 163, 184, 0.18)",
      },
      timeScale: {
        borderColor: "rgba(148, 163, 184, 0.18)",
        timeVisible: true,
      },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      borderUpColor: "#10b981",
      wickUpColor: "#34d399",
      downColor: "#fb7185",
      borderDownColor: "#fb7185",
      wickDownColor: "#fda4af",
    });
    let ignore = false;

    chartRef.current = chart;
    setState({ status: "loading", error: null });

    fetchDailyOhlcv(symbol, { range: "1y" })
      .then((bars) => {
        if (ignore) {
          return;
        }

        const chartData: CandlestickData[] = bars.map((bar) => ({
          time: toUtcTimestamp(bar.date),
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
        }));

        series.setData(chartData);
        chart.timeScale().fitContent();
        setState({ status: "ready", error: null });
      })
      .catch((error: unknown) => {
        if (ignore) {
          return;
        }

        setState({
          status: "error",
          error:
            error instanceof Error
              ? error.message
              : "Failed to load chart data",
        });
      });

    return () => {
      ignore = true;
      chart.remove();
      chartRef.current = null;
    };
  }, [symbol]);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Candlestick</h2>
          <p className="mt-1 text-xs text-slate-500">{symbol}</p>
        </div>
        <span className="rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium text-slate-400">
          Daily OHLCV
        </span>
      </div>
      <div className="relative h-80 min-h-80 overflow-hidden rounded-lg border border-white/10 bg-slate-950/40">
        <div className="absolute inset-0" ref={containerRef} />

        {state.status === "loading" && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70">
            <div className="w-52">
              <p className="text-center text-sm text-slate-300">
                Loading chart
              </p>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                <div className="h-full w-2/3 animate-pulse rounded-full bg-sky-400/70" />
              </div>
            </div>
          </div>
        )}

        {state.status === "error" && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 p-6 text-center">
            <div>
              <p className="text-sm font-medium text-rose-200">
                Chart data failed
              </p>
              <p className="mt-2 max-w-md text-sm text-rose-100/70">
                {state.error}
              </p>
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
