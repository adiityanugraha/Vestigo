import { fetchManyDailyOhlcv } from "./fetchData";
import {
  buildModelFeatureVector,
  predictStockProbability,
  type ModelPrediction,
} from "./mlInference";
import {
  screenStocks,
  type ScreenerCandidate,
  type ScreenerResult,
} from "./screener.ts";

export type PredictedScreenerCandidate = ScreenerCandidate & {
  prediction: ModelPrediction;
  predictionScore: number;
};

export type PredictionPipelineResult = {
  fetchedSymbols: number;
  predictedSymbols: number;
  rawScreener: ScreenerResult;
  bsjp: PredictedScreenerCandidate[];
  bpjs: PredictedScreenerCandidate[];
};

export async function runPredictionPipeline(
  symbols: readonly string[],
): Promise<PredictionPipelineResult> {
  const marketData = await fetchManyDailyOhlcv([...symbols], {
    range: "1y",
  });
  const rawScreener = screenStocks(marketData, { limit: 20 });
  const allCandidates = [...rawScreener.bsjp, ...rawScreener.bpjs];
  const predictionsBySymbol = new Map<string, ModelPrediction>();

  for (const [symbol, bars] of Object.entries(marketData)) {
    const featureVector = buildModelFeatureVector(bars);

    if (!featureVector) {
      continue;
    }

    predictionsBySymbol.set(symbol, await predictStockProbability(featureVector));
  }

  const predicted = await Promise.all(
    allCandidates.map(async (candidate) => {
      const prediction = predictionsBySymbol.get(candidate.current.symbol) ?? {
        label: 0,
        probabilityDown: 1,
        probabilityUp: 0,
      };

      return {
        ...candidate,
        prediction,
        predictionScore: prediction.probabilityUp * 100 + candidate.score,
      };
    }),
  );

  return {
    fetchedSymbols: Object.keys(marketData).length,
    predictedSymbols: predictionsBySymbol.size,
    rawScreener,
    bsjp: predicted
      .filter((candidate) => candidate.strategy === "BSJP")
      .sort((a, b) => b.predictionScore - a.predictionScore)
      .slice(0, 5),
    bpjs: predicted
      .filter((candidate) => candidate.strategy === "BPJS")
      .sort((a, b) => b.predictionScore - a.predictionScore)
      .slice(0, 5),
  };
}
