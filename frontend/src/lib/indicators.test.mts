import assert from "node:assert/strict";
import test from "node:test";
import {
  calculateAtr,
  calculateBollingerBands,
  calculateMacd,
  calculateRsi,
  calculateVolumeSpike,
  calculateVwap,
  simpleMovingAverage,
  type OhlcvBar,
} from "./indicators.ts";

const bars: OhlcvBar[] = [
  {
    symbol: "TEST.JK",
    date: "2026-01-01",
    open: 8,
    high: 10,
    low: 8,
    close: 9,
    volume: 100,
  },
  {
    symbol: "TEST.JK",
    date: "2026-01-02",
    open: 9,
    high: 11,
    low: 9,
    close: 10,
    volume: 100,
  },
  {
    symbol: "TEST.JK",
    date: "2026-01-03",
    open: 10,
    high: 13,
    low: 10,
    close: 12,
    volume: 100,
  },
  {
    symbol: "TEST.JK",
    date: "2026-01-04",
    open: 12,
    high: 14,
    low: 12,
    close: 13,
    volume: 250,
  },
];

test("simpleMovingAverage returns the latest rolling average", () => {
  assert.equal(simpleMovingAverage([1, 2, 3, 4], 3), 3);
});

test("calculateRsi returns 100 when all period changes are gains", () => {
  const result = calculateRsi([1, 2, 3, 4, 5], 3);

  assert.deepEqual(result.slice(0, 3), [null, null, null]);
  assert.equal(result[3], 100);
  assert.equal(result[4], 100);
});

test("calculateMacd returns MACD, signal, and histogram series", () => {
  const result = calculateMacd([1, 2, 3, 4, 5, 6], 2, 3, 2);

  assert.equal(result.macd[2], 0.5);
  assert.equal(result.macd[5], 0.5);
  assert.equal(result.signal[3], 0.5);
  assert.equal(result.histogram[5], 0);
});

test("calculateBollingerBands returns middle, upper, and lower bands", () => {
  const result = calculateBollingerBands([1, 2, 3], 3, 2);
  const latest = result[2];

  assert.equal(latest.middle, 2);
  assertAlmostEqual(latest.upper, 3.632993161855452);
  assertAlmostEqual(latest.lower, 0.36700683814454793);
});

test("calculateAtr returns Wilder-smoothed average true range", () => {
  const result = calculateAtr(bars, 3);

  assert.deepEqual(result.slice(0, 2), [null, null]);
  assertAlmostEqual(result[2], 2.3333333333333335);
  assertAlmostEqual(result[3], 2.2222222222222228);
});

test("calculateVwap returns cumulative volume weighted average price", () => {
  const result = calculateVwap([
    { ...bars[0], high: 2, low: 1, close: 1.5, volume: 100 },
    { ...bars[1], high: 4, low: 2, close: 3, volume: 100 },
  ]);

  assert.equal(result[0], 1.5);
  assert.equal(result[1], 2.25);
});

test("calculateVolumeSpike compares volume against previous rolling average", () => {
  const result = calculateVolumeSpike([100, 100, 100, 250], 3, 2);

  assert.deepEqual(result.slice(0, 3), [
    { ratio: null, isSpike: false },
    { ratio: null, isSpike: false },
    { ratio: null, isSpike: false },
  ]);
  assert.equal(result[3].ratio, 2.5);
  assert.equal(result[3].isSpike, true);
});

function assertAlmostEqual(
  actual: number | null,
  expected: number,
  epsilon = 1e-10,
) {
  assert.notEqual(actual, null);
  assert.ok(Math.abs(actual - expected) < epsilon);
}
