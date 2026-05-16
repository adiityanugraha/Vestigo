import assert from "node:assert/strict";
import test from "node:test";
import {
  buildScreenerInput,
  calculateTradeLevels,
  isBpjsCandidate,
  isBsjpCandidate,
  screenStocks,
} from "./screener.ts";
import type { OhlcvBar } from "./indicators.ts";

test("BSJP passes all blueprint criteria", () => {
  const input = buildScreenerInput(
    makeBars("BSJP.JK", [95, 96, 97, 98, 99, 100, 106], [
      40_000_000,
      40_000_000,
      40_000_000,
      40_000_000,
      40_000_000,
      40_000_000,
      60_000_000,
    ]),
  );

  assert.ok(input);
  assert.equal(isBsjpCandidate(input), true);
});

test("BPJS passes all blueprint criteria", () => {
  const input = buildScreenerInput(
    makeBars("BPJS.JK", [95, 96, 97, 98, 99, 100, 105], [
      100_000_000,
      100_000_000,
      100_000_000,
      100_000_000,
      100_000_000,
      100_000_000,
      50_000_000,
    ], {
      latestOpen: 104,
    }),
  );

  assert.ok(input);
  assert.equal(isBpjsCandidate(input), true);
});

test("candidate fails when daily value is below threshold", () => {
  const input = buildScreenerInput(
    makeBars("LOWV.JK", [95, 96, 97, 98, 99, 100, 106], [1_000, 1_000, 1_000, 1_000, 1_000, 1_000, 2_000]),
  );

  assert.ok(input);
  assert.equal(isBsjpCandidate(input), false);
  assert.equal(isBpjsCandidate(input), false);
});

test("screenStocks returns top strategy buckets from several sample stocks", () => {
  const result = screenStocks(
    {
      "BSJP.JK": makeBars("BSJP.JK", [95, 96, 97, 98, 99, 100, 106], [
        40_000_000,
        40_000_000,
        40_000_000,
        40_000_000,
        40_000_000,
        40_000_000,
        60_000_000,
      ]),
      "BPJS.JK": makeBars("BPJS.JK", [95, 96, 97, 98, 99, 100, 105], [
        100_000_000,
        100_000_000,
        100_000_000,
        100_000_000,
        100_000_000,
        100_000_000,
        50_000_000,
      ], {
        latestOpen: 104,
      }),
      "FAIL.JK": makeBars("FAIL.JK", [95, 96, 97, 98, 99, 100, 101], [1_000_000, 1_000_000, 1_000_000, 1_000_000, 1_000_000, 1_000_000, 100_000]),
    },
    { limit: 5 },
  );

  assert.equal(result.bsjp.length, 1);
  assert.equal(result.bpjs.length, 2);
  assert.equal(result.bsjp[0].current.symbol, "BSJP.JK");
  assert.equal(result.bpjs[0].levels.entry > 0, true);
});

test("calculateTradeLevels uses ATR risk with two-to-one reward", () => {
  const input = buildScreenerInput(
    makeBars("RISK.JK", [95, 96, 97, 98, 99, 100, 106], [
      40_000_000,
      40_000_000,
      40_000_000,
      40_000_000,
      40_000_000,
      40_000_000,
      60_000_000,
    ]),
  );

  assert.ok(input);

  const levels = calculateTradeLevels({ ...input, atr: 4 });

  assert.equal(levels.entry, 106);
  assert.equal(levels.stopLoss, 102);
  assert.equal(levels.takeProfit, 114);
  assert.equal(levels.exit, 114);
});

function makeBars(
  symbol: string,
  closes: number[],
  volumes: number[],
  options: { latestOpen?: number } = {},
): OhlcvBar[] {
  return closes.map((close, index) => {
    const isLatest = index === closes.length - 1;
    const open = isLatest && options.latestOpen ? options.latestOpen : close - 1;

    return {
      symbol,
      date: `2026-01-${String(index + 1).padStart(2, "0")}`,
      open,
      high: close + 2,
      low: close - 2,
      close,
      volume: volumes[index],
    };
  });
}
