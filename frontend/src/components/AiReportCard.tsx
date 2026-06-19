"use client";

import { getStockReport } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { useMode } from "./ModeProvider";
import { VCard } from "./vestigo/Card";
import { CardError, CardSkeleton } from "./CardStatus";

function sentimentTone(sentiment: string): "up" | "down" | "neutral" {
  if (sentiment === "Bullish") return "up";
  if (sentiment === "Bearish") return "down";
  return "neutral";
}

export function AiReportCard({ symbol }: { symbol: string }) {
  const { pro } = useMode();
  const { status, data, error, reload } = useApi(() => getStockReport(symbol), [symbol]);

  return (
    <VCard title="Verdict AI" sub={symbol} cached={!!data?.cached}>
      {status === "loading" && <CardSkeleton lines={4} />}
      {status === "error" && <CardError message={error} onRetry={reload} />}
      {status === "ready" && data && (
        <>
          <div className="verdict-top">
            <span className={`badge badge-${sentimentTone(data.sentiment)} badge-full`}>
              {data.sentiment}
            </span>
            <div className="ta-r">
              <p className="tile-label">AI Confidence</p>
              <p className="big-num mono">{data.score}%</p>
            </div>
          </div>

          <p className="verdict-summary">{data.summary}</p>

          {pro && (data.bullishFactors.length > 0 || data.riskFactors.length > 0) && (
            <div className="verdict-factors">
              {data.bullishFactors.length > 0 && (
                <div>
                  <p className="section-label">Faktor bullish</p>
                  <ul className="factor-list">
                    {data.bullishFactors.map((f) => (
                      <li key={f}>
                        <span className="fi fi-up">↑</span>
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {data.riskFactors.length > 0 && (
                <div>
                  <p className="section-label">Faktor risiko</p>
                  <ul className="factor-list">
                    {data.riskFactors.map((f) => (
                      <li key={f}>
                        <span className="fi fi-down">!</span>
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </VCard>
  );
}
