import { calculateTradeValue, type OhlcvBar } from "./indicators";

export type ScreenerInput = {
  current: OhlcvBar;
  previous: OhlcvBar;
  priceMa5: number;
};

export type ScreenerCandidate = ScreenerInput & {
  score: number;
  value: number;
};

const MIN_DAILY_VALUE = 5_000_000_000;

export function isBsjpCandidate(input: ScreenerInput): boolean {
  const { current, previous, priceMa5 } = input;
  const value = calculateTradeValue(current.close, current.volume);

  return (
    current.close >= 1.05 * previous.close &&
    current.close >= priceMa5 &&
    current.volume >= 1.2 * previous.volume &&
    value > MIN_DAILY_VALUE
  );
}

export function isBpjsCandidate(input: ScreenerInput): boolean {
  const { current, previous, priceMa5 } = input;
  const value = calculateTradeValue(current.close, current.volume);

  return (
    current.close >= priceMa5 &&
    current.close >= 1.05 * previous.close &&
    current.close >= current.open &&
    current.volume >= 0.2 * previous.volume &&
    value > MIN_DAILY_VALUE
  );
}

export function rankCandidates(inputs: ScreenerInput[], limit = 5): ScreenerCandidate[] {
  return inputs
    .map((input) => ({
      ...input,
      value: calculateTradeValue(input.current.close, input.current.volume),
      score:
        input.current.close / input.previous.close +
        input.current.volume / Math.max(input.previous.volume, 1),
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
