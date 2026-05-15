export type OhlcvBar = {
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type IndicatorValue = number | null;

export type MacdResult = {
  macd: IndicatorValue[];
  signal: IndicatorValue[];
  histogram: IndicatorValue[];
};

export type BollingerBand = {
  middle: IndicatorValue;
  upper: IndicatorValue;
  lower: IndicatorValue;
};

export type VolumeSpike = {
  ratio: IndicatorValue;
  isSpike: boolean;
};

export function simpleMovingAverage(values: number[], period: number): number | null {
  validatePeriod(period);

  if (values.length < period) {
    return null;
  }

  const window = values.slice(-period);
  const total = window.reduce((sum, value) => sum + value, 0);

  return total / period;
}

export function calculateRsi(closes: number[], period = 14): IndicatorValue[] {
  validatePeriod(period);

  const rsi = createNullSeries(closes.length);

  if (closes.length <= period) {
    return rsi;
  }

  let averageGain = 0;
  let averageLoss = 0;

  for (let index = 1; index <= period; index += 1) {
    const change = closes[index] - closes[index - 1];
    averageGain += Math.max(change, 0);
    averageLoss += Math.max(-change, 0);
  }

  averageGain /= period;
  averageLoss /= period;
  rsi[period] = calculateRsiValue(averageGain, averageLoss);

  for (let index = period + 1; index < closes.length; index += 1) {
    const change = closes[index] - closes[index - 1];
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);

    averageGain = (averageGain * (period - 1) + gain) / period;
    averageLoss = (averageLoss * (period - 1) + loss) / period;
    rsi[index] = calculateRsiValue(averageGain, averageLoss);
  }

  return rsi;
}

export function calculateMacd(
  closes: number[],
  fastPeriod = 12,
  slowPeriod = 26,
  signalPeriod = 9,
): MacdResult {
  validatePeriod(fastPeriod);
  validatePeriod(slowPeriod);
  validatePeriod(signalPeriod);

  if (fastPeriod >= slowPeriod) {
    throw new Error("MACD fastPeriod must be lower than slowPeriod");
  }

  const fastEma = calculateEma(closes, fastPeriod);
  const slowEma = calculateEma(closes, slowPeriod);
  const macd = closes.map((_, index) => {
    const fast = fastEma[index];
    const slow = slowEma[index];

    return fast === null || slow === null ? null : fast - slow;
  });
  const signal = calculateNullableEma(macd, signalPeriod);
  const histogram = macd.map((value, index) => {
    const signalValue = signal[index];

    return value === null || signalValue === null ? null : value - signalValue;
  });

  return { macd, signal, histogram };
}

export function calculateBollingerBands(
  closes: number[],
  period = 20,
  multiplier = 2,
): BollingerBand[] {
  validatePeriod(period);

  return closes.map((_, index) => {
    if (index + 1 < period) {
      return { middle: null, upper: null, lower: null };
    }

    const window = closes.slice(index + 1 - period, index + 1);
    const middle = average(window);
    const standardDeviation = Math.sqrt(
      average(window.map((value) => (value - middle) ** 2)),
    );

    return {
      middle,
      upper: middle + standardDeviation * multiplier,
      lower: middle - standardDeviation * multiplier,
    };
  });
}

export function calculateAtr(bars: OhlcvBar[], period = 14): IndicatorValue[] {
  validatePeriod(period);

  const trueRanges = bars.map((bar, index) => {
    if (index === 0) {
      return bar.high - bar.low;
    }

    const previousClose = bars[index - 1].close;

    return Math.max(
      bar.high - bar.low,
      Math.abs(bar.high - previousClose),
      Math.abs(bar.low - previousClose),
    );
  });
  const atr = createNullSeries(bars.length);

  if (trueRanges.length < period) {
    return atr;
  }

  let currentAtr = average(trueRanges.slice(0, period));
  atr[period - 1] = currentAtr;

  for (let index = period; index < trueRanges.length; index += 1) {
    currentAtr = (currentAtr * (period - 1) + trueRanges[index]) / period;
    atr[index] = currentAtr;
  }

  return atr;
}

export function calculateVwap(bars: OhlcvBar[]): IndicatorValue[] {
  let cumulativeTypicalPriceVolume = 0;
  let cumulativeVolume = 0;

  return bars.map((bar) => {
    const typicalPrice = (bar.high + bar.low + bar.close) / 3;

    cumulativeTypicalPriceVolume += typicalPrice * bar.volume;
    cumulativeVolume += bar.volume;

    return cumulativeVolume === 0
      ? null
      : cumulativeTypicalPriceVolume / cumulativeVolume;
  });
}

export function calculateVolumeSpike(
  volumes: number[],
  period = 20,
  multiplier = 1.5,
): VolumeSpike[] {
  validatePeriod(period);

  return volumes.map((volume, index) => {
    if (index < period) {
      return { ratio: null, isSpike: false };
    }

    const baseline = average(volumes.slice(index - period, index));
    const ratio = baseline === 0 ? null : volume / baseline;

    return {
      ratio,
      isSpike: ratio !== null && ratio >= multiplier,
    };
  });
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

function calculateEma(values: number[], period: number): IndicatorValue[] {
  const ema = createNullSeries(values.length);

  if (values.length < period) {
    return ema;
  }

  const smoothing = 2 / (period + 1);
  let previousEma = average(values.slice(0, period));
  ema[period - 1] = previousEma;

  for (let index = period; index < values.length; index += 1) {
    previousEma = values[index] * smoothing + previousEma * (1 - smoothing);
    ema[index] = previousEma;
  }

  return ema;
}

function calculateNullableEma(
  values: IndicatorValue[],
  period: number,
): IndicatorValue[] {
  const ema = createNullSeries(values.length);
  const validValues: number[] = [];
  const validIndexes: number[] = [];

  values.forEach((value, index) => {
    if (value !== null) {
      validValues.push(value);
      validIndexes.push(index);
    }
  });

  const compactEma = calculateEma(validValues, period);

  compactEma.forEach((value, index) => {
    ema[validIndexes[index]] = value;
  });

  return ema;
}

function calculateRsiValue(averageGain: number, averageLoss: number): number {
  if (averageLoss === 0) {
    return 100;
  }

  if (averageGain === 0) {
    return 0;
  }

  const relativeStrength = averageGain / averageLoss;

  return 100 - 100 / (1 + relativeStrength);
}

function average(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function createNullSeries(length: number): IndicatorValue[] {
  return Array.from({ length }, () => null);
}

function validatePeriod(period: number) {
  if (!Number.isInteger(period) || period <= 0) {
    throw new Error("Indicator period must be a positive integer");
  }
}
