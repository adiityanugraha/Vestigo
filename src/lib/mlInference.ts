import * as ort from "onnxruntime-web";
import {
  calculateAtr,
  calculateBollingerBands,
  calculateMacd,
  calculateRsi,
  calculateVwap,
  simpleMovingAverage,
  type OhlcvBar,
} from "./indicators.ts";

export const MODEL_FEATURE_COLUMNS = [
  "return_1d",
  "return_5d",
  "ma5_ratio",
  "ma20_ratio",
  "volume_ratio_20",
  "value_log",
  "rsi_14",
  "macd",
  "macd_signal",
  "macd_histogram",
  "bb_position",
  "atr_pct",
  "vwap_ratio",
] as const;

export type ModelFeatureName = (typeof MODEL_FEATURE_COLUMNS)[number];

export type ModelPrediction = {
  label: number;
  probabilityDown: number;
  probabilityUp: number;
};

let sessionPromise: Promise<ort.InferenceSession> | null = null;
let inferenceQueue: Promise<void> = Promise.resolve();

export async function loadModelSession(modelPath = "/model.onnx") {
  configureOnnxRuntime();

  sessionPromise ??= ort.InferenceSession.create(modelPath, {
    executionProviders: ["wasm"],
  });

  return sessionPromise;
}

export function buildModelFeatureVector(bars: OhlcvBar[]): number[] | null {
  if (bars.length < 30) {
    return null;
  }

  const current = bars.at(-1);
  const previous = bars.at(-2);
  const closeFiveDaysAgo = bars.at(-6);

  if (!current || !previous || !closeFiveDaysAgo) {
    return null;
  }

  const closes = bars.map((bar) => bar.close);
  const volumes = bars.map((bar) => bar.volume);
  const ma5 = simpleMovingAverage(closes, 5);
  const ma20 = simpleMovingAverage(closes, 20);
  const volumeMa20 = simpleMovingAverage(volumes, 20);
  const rsi14 = calculateRsi(closes, 14).at(-1);
  const macd = calculateMacd(closes);
  const bollinger = calculateBollingerBands(closes, 20).at(-1);
  const atr = calculateAtr(bars, 14).at(-1);
  const vwap = calculateVwap(bars).at(-1);

  if (!ma5 || !ma20 || !volumeMa20 || !bollinger) {
    return null;
  }

  const bandRange =
    bollinger.upper === null || bollinger.lower === null
      ? null
      : bollinger.upper - bollinger.lower;

  const features: Record<ModelFeatureName, number | null> = {
    return_1d: current.close / previous.close - 1,
    return_5d: current.close / closeFiveDaysAgo.close - 1,
    ma5_ratio: current.close / ma5 - 1,
    ma20_ratio: current.close / ma20 - 1,
    volume_ratio_20: current.volume / volumeMa20,
    value_log: Math.log1p(current.close * current.volume),
    rsi_14: rsi14 ?? null,
    macd: macd.macd.at(-1) ?? null,
    macd_signal: macd.signal.at(-1) ?? null,
    macd_histogram: macd.histogram.at(-1) ?? null,
    bb_position:
      bandRange === null || bandRange === 0 || bollinger.lower === null
        ? null
        : (current.close - bollinger.lower) / bandRange,
    atr_pct: atr == null ? null : atr / current.close,
    vwap_ratio: vwap == null ? null : current.close / vwap - 1,
  };

  return MODEL_FEATURE_COLUMNS.map((column) => sanitizeFeature(features[column]));
}

export async function predictStockProbability(
  featureVector: number[],
): Promise<ModelPrediction> {
  const predictionTask = inferenceQueue.then(() => runQueuedInference(featureVector));

  inferenceQueue = predictionTask.then(
    () => undefined,
    () => undefined,
  );

  return predictionTask;
}

async function runQueuedInference(featureVector: number[]): Promise<ModelPrediction> {
  const session = await loadModelSession();
  const tensor = new ort.Tensor("float32", Float32Array.from(featureVector), [
    1,
    featureVector.length,
  ]);
  const outputs = await session.run({ [session.inputNames[0]]: tensor });
  const labelOutput = outputs[session.outputNames[0]];
  const probabilityOutput = outputs[session.outputNames[1]];
  const probabilities = Array.from(probabilityOutput.data as Float32Array);

  return {
    label: Number(labelOutput.data[0]),
    probabilityDown: probabilities[0] ?? 0,
    probabilityUp: probabilities[1] ?? 0,
  };
}

function configureOnnxRuntime() {
  ort.env.wasm.wasmPaths = "/onnxruntime/";
  ort.env.wasm.numThreads = 1;
}

function sanitizeFeature(value: number | null | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}
