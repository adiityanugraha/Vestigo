"""Fetch data fundamental dari Yahoo Finance quoteSummary (Phase 3 Day 4).

Sumber data fundamental Phase 3 = Yahoo (gratis, reuse pipeline yang sudah ada).
Berbeda dari endpoint chart (OHLCV) di app.core.yahoo, endpoint quoteSummary
butuh autentikasi cookie + crumb (anti-bot Yahoo sejak 2023). Modul ini:

  1. Membangun sesi: GET halaman Yahoo -> set cookie -> ambil crumb.
  2. Memanggil quoteSummary dengan modul yang relevan + crumb.
  3. Memetakan respons ke FundamentalSnapshot.
  4. Menyimpan ke tabel `fundamentals` (baris ANNUAL historis + 1 baris TTM).

KETERBATASAN data Yahoo untuk IDX (penting untuk Day 6-7):
  - ANDAL  : totalRevenue, grossProfits(TTM), returnOnEquity, totalCash,
             totalDebt, marketCap, trailingPE, PBV, dividendYield/Rate, EPS,
             dan revenue+net_income tahunan (4 tahun) dari incomeStatementHistory.
  - TIDAK ANDAL (sering None/0, dibiarkan None): operatingIncome & grossProfit
             per-tahun, semua field balanceSheetHistory (equity/cash per-periode),
             dividend payment streak.
  - common_equity diturunkan dari marketCap / PBV (price saling meniadakan,
             jadi nilainya tidak bergantung harga).

Jalankan manual (seed beberapa saham uji):
    python -m app.data.fundamentals_fetch --ticker BBCA BMRI ASII TLKM UNVR
    python -m app.data.fundamentals_fetch --limit 10
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models import Fundamental, Stock
from app.db.session import SessionLocal
from app.core.yahoo import to_yahoo_symbol

# Modul quoteSummary yang dibutuhkan (gabungan agregat TTM + histori tahunan).
QUOTE_SUMMARY_MODULES = (
    "summaryDetail",
    "defaultKeyStatistics",
    "financialData",
    "incomeStatementHistory",
)
QUOTE_SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
COOKIE_URLS = ("https://fc.yahoo.com", "https://finance.yahoo.com")
CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


class YahooFundamentalsError(RuntimeError):
    """Gagal mengambil / mem-parse data fundamental satu simbol."""


@dataclass(frozen=True)
class AnnualRecord:
    """Satu periode tahunan dari incomeStatementHistory."""

    period: str  # tahun fiskal, mis. "2025"
    revenue: float | None
    net_income: float | None


@dataclass(frozen=True)
class FundamentalSnapshot:
    """Hasil terstruktur fetch fundamental satu ticker."""

    ticker: str
    annual: list[AnnualRecord] = field(default_factory=list)
    # Agregat TTM / saat ini
    revenue_ttm: float | None = None
    gross_profit_ttm: float | None = None
    income_from_operations: float | None = None
    common_equity: float | None = None
    cash_equivalents: float | None = None
    total_debt: float | None = None
    roe: float | None = None
    eps: float | None = None
    dps: float | None = None
    # Harga-sensitif (untuk Day 5 fundamental_derived, dibawa di sini sekalian)
    market_cap: float | None = None
    pbv: float | None = None
    trailing_pe: float | None = None
    dividend_yield: float | None = None


def _raw(node: dict | None, key: str) -> float | None:
    """Yahoo membungkus angka sebagai {'raw': x, 'fmt': ...}; ambil 'raw'."""
    if not node:
        return None
    value = node.get(key)
    if isinstance(value, dict):
        value = value.get("raw")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _nonzero(value: float | None) -> float | None:
    """Yahoo kadang mengembalikan 0 untuk field IDX yang sebenarnya kosong."""
    return value if value not in (None, 0) else None


class YahooFundamentalsClient:
    """Klien quoteSummary dengan manajemen cookie + crumb dan retry refresh."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._owns = client is None
        self._client = client or httpx.Client(
            headers=_HEADERS, timeout=20.0, follow_redirects=True
        )
        self._crumb: str | None = None

    def close(self) -> None:
        if self._owns:
            self._client.close()

    def __enter__(self) -> YahooFundamentalsClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _refresh_crumb(self) -> str:
        for url in COOKIE_URLS:
            try:
                self._client.get(url)
            except httpx.HTTPError:
                continue  # fc.yahoo.com sering 404 tapi tetap set cookie
        resp = self._client.get(CRUMB_URL)
        crumb = resp.text.strip()
        if resp.status_code != 200 or not crumb or "<html" in crumb.lower():
            raise YahooFundamentalsError("Gagal memperoleh crumb Yahoo.")
        self._crumb = crumb
        return crumb

    def _get_summary(self, symbol: str) -> dict:
        """Panggil quoteSummary; refresh crumb sekali bila 401 (crumb basi)."""
        if self._crumb is None:
            self._refresh_crumb()

        url = QUOTE_SUMMARY_URL.format(symbol=symbol)
        params = {"modules": ",".join(QUOTE_SUMMARY_MODULES), "crumb": self._crumb}
        for attempt in (1, 2):
            try:
                resp = self._client.get(url, params=params)
            except httpx.HTTPError as exc:
                raise YahooFundamentalsError(f"Request gagal untuk {symbol}: {exc}") from exc
            if resp.status_code == 401 and attempt == 1:
                params["crumb"] = self._refresh_crumb()  # crumb kedaluwarsa
                time.sleep(0.4)
                continue
            if resp.status_code != 200:
                raise YahooFundamentalsError(
                    f"quoteSummary {symbol} -> HTTP {resp.status_code}: {resp.text[:120]}"
                )
            payload = resp.json()
            result = (payload.get("quoteSummary") or {}).get("result")
            if not result:
                error = (payload.get("quoteSummary") or {}).get("error")
                raise YahooFundamentalsError(f"quoteSummary {symbol} kosong: {error}")
            return result[0]
        raise YahooFundamentalsError(f"quoteSummary {symbol} gagal setelah refresh crumb.")

    def fetch(self, ticker: str) -> FundamentalSnapshot:
        symbol = to_yahoo_symbol(ticker)
        result = self._get_summary(symbol)
        return parse_summary_result(ticker, result)


def parse_summary_result(ticker: str, result: dict) -> FundamentalSnapshot:
    """Petakan satu objek quoteSummary.result -> FundamentalSnapshot (fungsi murni)."""
    fin = result.get("financialData") or {}
    summary = result.get("summaryDetail") or {}
    stats = result.get("defaultKeyStatistics") or {}
    income = (result.get("incomeStatementHistory") or {}).get(
        "incomeStatementHistory"
    ) or []

    annual: list[AnnualRecord] = []
    for statement in income:
        end = statement.get("endDate") or {}
        fmt = end.get("fmt")  # "2025-12-31"
        period = fmt[:4] if fmt else "?"
        annual.append(
            AnnualRecord(
                period=period,
                revenue=_raw(statement, "totalRevenue"),
                net_income=_raw(statement, "netIncome"),
            )
        )

    market_cap = _raw(summary, "marketCap")
    # PBV: defaultKeyStatistics lebih konsisten daripada summaryDetail untuk IDX.
    pbv = _raw(stats, "priceToBook") or _raw(summary, "priceToBook")
    # common_equity = marketCap / PBV (price saling meniadakan -> tak harga-sensitif).
    common_equity = (market_cap / pbv) if (market_cap and pbv) else None

    return FundamentalSnapshot(
        ticker=ticker.strip().upper(),
        annual=annual,
        revenue_ttm=_raw(fin, "totalRevenue"),
        gross_profit_ttm=_nonzero(_raw(fin, "grossProfits")),
        income_from_operations=_nonzero(_raw(fin, "operatingIncome")),
        common_equity=common_equity,
        cash_equivalents=_raw(fin, "totalCash"),
        total_debt=_raw(fin, "totalDebt"),
        roe=_raw(fin, "returnOnEquity"),
        eps=_raw(stats, "trailingEps"),
        dps=_raw(summary, "dividendRate"),
        market_cap=market_cap,
        pbv=pbv,
        trailing_pe=_raw(summary, "trailingPE"),
        dividend_yield=_raw(summary, "dividendYield"),
    )


# --------------------------------------------------------------------------- #
# Persistensi ke tabel fundamentals
# --------------------------------------------------------------------------- #
_UPSERT_COLUMNS = (
    "revenue",
    "net_income",
    "income_from_operations",
    "gross_profit",
    "common_equity",
    "cash_equivalents",
    "total_debt",
    "roe",
    "eps",
    "dps",
    "dividend_streak",
    "updated_at",
)


def snapshot_to_rows(snap: FundamentalSnapshot) -> list[dict]:
    """Pecah snapshot jadi baris fundamentals: N baris ANNUAL + 1 baris TTM."""
    now = datetime.now(timezone.utc)
    rows: list[dict] = []

    for record in snap.annual:
        rows.append(
            {
                "ticker": snap.ticker,
                "period": record.period,
                "report_type": "ANNUAL",
                "revenue": record.revenue,
                "net_income": record.net_income,
                "income_from_operations": None,
                "gross_profit": None,
                "common_equity": None,
                "cash_equivalents": None,
                "total_debt": None,
                "roe": None,
                "eps": None,
                "dps": None,
                "dividend_streak": None,
                "updated_at": now,
            }
        )

    rows.append(
        {
            "ticker": snap.ticker,
            "period": "TTM",
            "report_type": "TTM",
            "revenue": snap.revenue_ttm,
            "net_income": snap.annual[0].net_income if snap.annual else None,
            "income_from_operations": snap.income_from_operations,
            "gross_profit": snap.gross_profit_ttm,
            "common_equity": snap.common_equity,
            "cash_equivalents": snap.cash_equivalents,
            "total_debt": snap.total_debt,
            "roe": snap.roe,
            "eps": snap.eps,
            "dps": snap.dps,
            "dividend_streak": None,
            "updated_at": now,
        }
    )
    return rows


def upsert_fundamental_rows(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = pg_insert(Fundamental).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_fundamentals_ticker_period_type",
        set_={column: stmt.excluded[column] for column in _UPSERT_COLUMNS},
    )
    db.execute(stmt)


def ingest_ticker(db: Session, ticker: str, client: YahooFundamentalsClient) -> int:
    snap = client.fetch(ticker)
    rows = snapshot_to_rows(snap)
    upsert_fundamental_rows(db, rows)
    db.commit()
    return len(rows)


def ingest_fundamentals(
    db: Session, tickers: list[str] | None = None, delay: float = 0.8
) -> dict[str, int]:
    """Ingest fundamental banyak ticker. Error per-ticker di-skip (tak menggagalkan batch)."""
    if tickers is None:
        tickers = list(db.scalars(select(Stock.ticker).order_by(Stock.ticker)))

    results: dict[str, int] = {}
    with YahooFundamentalsClient() as client:
        for index, ticker in enumerate(tickers, start=1):
            try:
                count = ingest_ticker(db, ticker, client)
                results[ticker] = count
                print(f"  [{index:>3}/{len(tickers)}] {ticker:<6} -> {count} baris")
            except YahooFundamentalsError as exc:
                db.rollback()
                results[ticker] = 0
                print(f"  [{index:>3}/{len(tickers)}] {ticker:<6} -> SKIP ({exc})")
            if delay:
                time.sleep(delay)
    return results


def _main() -> None:
    parser = argparse.ArgumentParser(description="Ingest data fundamental dari Yahoo")
    parser.add_argument("--ticker", nargs="+", help="Ticker spesifik (mis. BBCA BMRI).")
    parser.add_argument("--limit", type=int, help="Batasi N ticker pertama dari stocks.")
    parser.add_argument("--delay", type=float, default=0.8, help="Jeda antar fetch (detik).")
    args = parser.parse_args()

    if SessionLocal is None:
        raise SystemExit("DATABASE_URL belum diset di backend/.env")

    db = SessionLocal()
    try:
        tickers = args.ticker
        if tickers is None and args.limit:
            tickers = list(
                db.scalars(select(Stock.ticker).order_by(Stock.ticker).limit(args.limit))
            )
        print("Mulai ingest fundamental...")
        results = ingest_fundamentals(db, tickers=tickers, delay=args.delay)
        ok = sum(1 for c in results.values() if c > 0)
        total = sum(results.values())
        print(f"\nSelesai: {ok}/{len(results)} ticker berhasil, {total} baris fundamentals.")
    finally:
        db.close()


if __name__ == "__main__":
    _main()
