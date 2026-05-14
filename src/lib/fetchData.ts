import type { OhlcvBar } from "./indicators";

type YahooFinanceBar = {
  timestamp: number[];
  indicators: {
    quote: Array<{
      open: Array<number | null>;
      high: Array<number | null>;
      low: Array<number | null>;
      close: Array<number | null>;
      volume: Array<number | null>;
    }>;
  };
};

type YahooFinanceResponse = {
  chart: {
    result: YahooFinanceBar[] | null;
    error: unknown;
  };
};

export async function fetchDailyOhlcv(symbol: string): Promise<OhlcvBar[]> {
  const yahooSymbol = symbol.endsWith(".JK") ? symbol : `${symbol}.JK`;
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${yahooSymbol}?range=6mo&interval=1d`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch market data for ${symbol}`);
  }

  const payload = (await response.json()) as YahooFinanceResponse;
  const result = payload.chart.result?.[0];

  if (!result) {
    return [];
  }

  const quote = result.indicators.quote[0];

  return result.timestamp.flatMap((timestamp, index) => {
    const open = quote.open[index];
    const high = quote.high[index];
    const low = quote.low[index];
    const close = quote.close[index];
    const volume = quote.volume[index];

    if (
      open === null ||
      high === null ||
      low === null ||
      close === null ||
      volume === null
    ) {
      return [];
    }

    return {
      symbol: yahooSymbol,
      date: new Date(timestamp * 1000).toISOString().slice(0, 10),
      open,
      high,
      low,
      close,
      volume,
    };
  });
}
