"""Refresh metrik fundamental harga-sensitif harian (Phase 3 Day 5).

Mengisi tabel fundamental_derived (pe_annualised, pbv, market_cap, dividend_yield)
dengan menggabungkan baris fundamentals (TTM) + harga penutupan TERBARU dari
market_data. Dipanggil scheduler 07:15 (Day 13) dan bisa manual:

    python -m app.data.fundamentals_derived            # semua ticker berfundamental
    python -m app.data.fundamentals_derived --ticker BBCA ASII
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.fundamentals import build_fundamental_view
from app.db.models import Fundamental, FundamentalDerived, MarketData
from app.db.session import SessionLocal

_UPSERT_COLUMNS = ("pe_annualised", "pbv", "market_cap", "dividend_yield", "updated_at")


def _latest_close(db: Session, ticker: str) -> tuple[float | None, object | None]:
    row = db.execute(
        select(MarketData.close, MarketData.date)
        .where(MarketData.ticker == ticker)
        .order_by(MarketData.date.desc())
        .limit(1)
    ).first()
    return (row[0], row[1]) if row else (None, None)


def tickers_with_fundamentals(db: Session) -> list[str]:
    return list(db.scalars(select(Fundamental.ticker).distinct().order_by(Fundamental.ticker)))


def refresh_derived(db: Session, tickers: list[str] | None = None) -> dict[str, bool]:
    """Hitung & upsert fundamental_derived untuk tiap ticker. True bila tersimpan."""
    if tickers is None:
        tickers = tickers_with_fundamentals(db)

    now = datetime.now(timezone.utc)
    results: dict[str, bool] = {}
    for ticker in tickers:
        rows = list(db.scalars(select(Fundamental).where(Fundamental.ticker == ticker)))
        close, as_of = _latest_close(db, ticker)
        if not rows or close is None or as_of is None:
            results[ticker] = False
            continue

        view = build_fundamental_view(ticker, rows, close=close, as_of=as_of)
        stmt = pg_insert(FundamentalDerived).values(
            ticker=ticker,
            date=as_of,
            pe_annualised=view.pe_annualised,
            pbv=view.pbv,
            market_cap=view.market_cap,
            dividend_yield=view.dividend_yield,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_fundamental_derived_ticker_date",
            set_={c: stmt.excluded[c] for c in _UPSERT_COLUMNS},
        )
        db.execute(stmt)
        results[ticker] = True

    db.commit()
    return results


def _main() -> None:
    parser = argparse.ArgumentParser(description="Refresh fundamental_derived (harga-sensitif)")
    parser.add_argument("--ticker", nargs="+", help="Ticker spesifik. Default: semua berfundamental.")
    args = parser.parse_args()

    if SessionLocal is None:
        raise SystemExit("DATABASE_URL belum diset di backend/.env")

    db = SessionLocal()
    try:
        results = refresh_derived(db, tickers=args.ticker)
        ok = sum(1 for v in results.values() if v)
        print(f"fundamental_derived: {ok}/{len(results)} ticker ter-refresh.")
        for ticker, saved in results.items():
            if not saved:
                print(f"  SKIP {ticker} (fundamentals / harga tidak lengkap)")
    finally:
        db.close()


if __name__ == "__main__":
    _main()
