export type OhlcvBar = {
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export function simpleMovingAverage(values: number[], period: number): number | null {
  if (values.length < period) {
    return null;
  }

  const window = values.slice(-period);
  const total = window.reduce((sum, value) => sum + value, 0);

  return total / period;
}

export function calculateTradeValue(price: number, volume: number): number {
  return price * volume;
}

export function estimateAtrRiskLevels(price: number, atr: number) {
  return {
    entry: price,
    stopLoss: price - atr,
    takeProfit: price + atr * 2,
  };
}
