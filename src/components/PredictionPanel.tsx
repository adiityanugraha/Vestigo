"use client";

import { useEffect, useState } from "react";
import { runPredictionPipeline, type PredictionPipelineResult } from "@/lib/predictionPipeline";
import { IDX_WATCHLIST } from "@/lib/watchlist";
import { ScreenerTable } from "./ScreenerTable";

type PredictionState =
  | { status: "loading"; result: null; error: null }
  | { status: "ready"; result: PredictionPipelineResult; error: null }
  | { status: "error"; result: null; error: string };

type PredictionPanelProps = {
  onSelectSymbol: (symbol: string) => void;
  selectedSymbol: string;
};

export function PredictionPanel({
  onSelectSymbol,
  selectedSymbol,
}: PredictionPanelProps) {
  const [state, setState] = useState<PredictionState>({
    status: "loading",
    result: null,
    error: null,
  });

  function runPipeline() {
    setState({ status: "loading", result: null, error: null });

    return runPredictionPipeline(IDX_WATCHLIST)
      .then((result) => {
        setState({ status: "ready", result, error: null });
      })
      .catch((error: unknown) => {
        setState({
          status: "error",
          result: null,
          error:
            error instanceof Error
              ? error.message
              : "Prediction pipeline failed",
        });
      });
  }

  useEffect(() => {
    let ignore = false;

    runPredictionPipeline(IDX_WATCHLIST)
      .then((result) => {
        if (!ignore) {
          setState({ status: "ready", result, error: null });
        }
      })
      .catch((error: unknown) => {
        if (!ignore) {
          setState({
            status: "error",
            result: null,
            error:
              error instanceof Error
                ? error.message
                : "Prediction pipeline failed",
          });
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <section className="flex flex-col gap-6">
      <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
        <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-base font-semibold text-white">ML Screener</h2>
            <p className="mt-1 text-sm text-slate-400">
              Data, indicators, ONNX inference, ranking
            </p>
          </div>
          <span className="rounded-md border border-white/10 px-3 py-1 text-xs font-medium text-slate-300">
            {state.status}
          </span>
        </div>

        {state.status === "loading" && (
          <div className="mt-5 grid gap-3 sm:grid-cols-4">
            {["Market data", "Indicators", "ONNX model", "Ranking"].map(
              (label) => (
                <div
                  className="h-20 rounded-lg border border-white/10 bg-slate-950/60 p-4"
                  key={label}
                >
                  <p className="text-xs text-slate-500">{label}</p>
                  <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/10">
                    <div className="h-full w-2/3 animate-pulse rounded-full bg-sky-400/70" />
                  </div>
                </div>
              ),
            )}
          </div>
        )}

        {state.status === "error" && (
          <div className="mt-5 rounded-lg border border-rose-400/30 bg-rose-500/10 p-4">
            <p className="text-sm font-medium text-rose-200">
              Pipeline failed
            </p>
            <p className="mt-1 text-sm text-rose-100/80">{state.error}</p>
            <button
              className="mt-4 rounded-lg border border-rose-300/30 px-3 py-2 text-sm font-medium text-rose-100 transition-colors hover:bg-rose-400/10"
              onClick={() => {
                void runPipeline();
              }}
              type="button"
            >
              Retry
            </button>
          </div>
        )}

        {state.status === "ready" && (
          <div className="mt-4 grid gap-3 text-sm text-slate-300 sm:grid-cols-4">
            <p>{state.result.fetchedSymbols} symbols fetched</p>
            <p>{state.result.predictedSymbols} ONNX scored</p>
            <p>{state.result.bsjp.length} BSJP ranked</p>
            <p>{state.result.bpjs.length} BPJS ranked</p>
          </div>
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <ScreenerTable
          isLoading={state.status === "loading"}
          onSelectSymbol={onSelectSymbol}
          selectedSymbol={selectedSymbol}
          title="Top 5 BSJP"
          rows={state.status === "ready" ? state.result.bsjp : []}
        />
        <ScreenerTable
          isLoading={state.status === "loading"}
          onSelectSymbol={onSelectSymbol}
          selectedSymbol={selectedSymbol}
          title="Top 5 BPJS"
          rows={state.status === "ready" ? state.result.bpjs : []}
        />
      </div>
    </section>
  );
}
