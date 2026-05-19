"use client";

import { useEffect, useState } from "react";
import { runPredictionPipeline, type PredictionPipelineResult } from "@/lib/predictionPipeline";
import { IDX_WATCHLIST } from "@/lib/watchlist";
import { ScreenerTable } from "./ScreenerTable";

type PredictionState =
  | { status: "loading"; result: null; error: null }
  | { status: "ready"; result: PredictionPipelineResult; error: null }
  | { status: "error"; result: null; error: string };

export function PredictionPanel() {
  const [state, setState] = useState<PredictionState>({
    status: "loading",
    result: null,
    error: null,
  });

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
      <div className="rounded-lg border border-white/10 bg-white/[0.03] p-5">
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
          <p className="mt-4 text-sm text-slate-400">
            Running IDX watchlist pipeline...
          </p>
        )}

        {state.status === "error" && (
          <p className="mt-4 text-sm text-rose-300">{state.error}</p>
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
          title="Top 5 BSJP"
          rows={state.status === "ready" ? state.result.bsjp : []}
        />
        <ScreenerTable
          title="Top 5 BPJS"
          rows={state.status === "ready" ? state.result.bpjs : []}
        />
      </div>
    </section>
  );
}
