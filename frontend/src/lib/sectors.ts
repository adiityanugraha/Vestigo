export type Sector =
  | "Banking"
  | "Telco"
  | "Consumer"
  | "Energy"
  | "Metals"
  | "Industrials";

// Sektor untuk universe saham yang dipakai screener & backtesting (lihat
// public/backtesting/*.json). Dipetakan manual karena Phase 1 belum punya
// backend / data sektor resmi.
export const SECTOR_BY_SYMBOL: Record<string, Sector> = {
  "BBCA.JK": "Banking",
  "BBRI.JK": "Banking",
  "BMRI.JK": "Banking",
  "BRIS.JK": "Banking",
  "TLKM.JK": "Telco",
  "UNVR.JK": "Consumer",
  "ICBP.JK": "Consumer",
  "INDF.JK": "Consumer",
  "CPIN.JK": "Consumer",
  "ANTM.JK": "Metals",
  "MDKA.JK": "Metals",
  "INCO.JK": "Metals",
  "ADRO.JK": "Energy",
  "PGAS.JK": "Energy",
  "ASII.JK": "Industrials",
};

export const SECTORS: Sector[] = [
  "Banking",
  "Consumer",
  "Metals",
  "Energy",
  "Telco",
  "Industrials",
];

export function getSector(symbol: string): Sector | undefined {
  return SECTOR_BY_SYMBOL[symbol.trim().toUpperCase()];
}
