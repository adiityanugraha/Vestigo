"""Fundamentals API (Phase 3 Day 5).

GET /api/fundamentals/{ticker}
  Gabungkan baris tabel `fundamentals` (TTM + histori tahunan) dengan harga
  terbaru market_data -> FundamentalView (raw + metrik harga-sensitif + growth).
  Hasil di-cache di Redis (TTL_REPORT). Field yang tak tersedia dari Yahoo
  gratis (roe_5yr_avg, dividend_streak) dikembalikan null + ditandai di
  `availability` agar konsumen tahu keterbatasannya.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.core.fundamentals import build_fundamental_view
from app.db.models import Fundamental, MarketData, Stock
from app.db.session import get_db

router = APIRouter(prefix="/api/fundamentals", tags=["fundamentals"])

CACHE_KEY = "fundamentals:{ticker}"


class AnnualPointOut(BaseModel):
    period: str
    revenue: float | None = None
    net_income: float | None = None


class GrowthOut(BaseModel):
    revenue_growth_yoy: float | None = None
    revenue_growth_3yr: float | None = None
    net_income_growth_yoy: float | None = None
    net_income_growth_3yr: float | None = None
    sales_growth_streak: int = 0


class DerivedOut(BaseModel):
    close: float | None = None
    date: str | None = None
    shares_outstanding: float | None = None
    market_cap: float | None = None
    pe_annualised: float | None = None
    pbv: float | None = None
    dividend_yield: float | None = None


class RawOut(BaseModel):
    revenue_ttm: float | None = None
    net_income_ttm: float | None = None
    gross_profit: float | None = None
    income_from_operations: float | None = None
    common_equity: float | None = None
    cash_equivalents: float | None = None
    total_debt: float | None = None
    roe: float | None = None
    eps: float | None = None
    dps: float | None = None


class AvailabilityOut(BaseModel):
    """Penanda keterbatasan data (Yahoo gratis) agar UI bisa memberi disclaimer."""

    roe_5yr_avg: bool
    dividend_streak: bool
    income_from_operations: bool
    price_return_is_10yr: bool
    price_return_span_days: int | None = None


class FundamentalsResponse(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    raw: RawOut
    derived: DerivedOut
    growth: GrowthOut
    annual: list[AnnualPointOut]
    roe_5yr_avg: float | None = None
    dividend_streak: int | None = None
    price_return: float | None = None
    availability: AvailabilityOut
    cached: bool
    generated_at: str


def _build_payload(ticker: str, rows: list[Fundamental], db: Session) -> dict:
    latest = db.execute(
        select(MarketData.close, MarketData.date)
        .where(MarketData.ticker == ticker)
        .order_by(MarketData.date.desc())
        .limit(1)
    ).first()
    close = latest[0] if latest else None
    as_of = latest[1] if latest else None

    price_bars = list(
        db.scalars(
            select(MarketData).where(MarketData.ticker == ticker).order_by(MarketData.date)
        )
    )
    view = build_fundamental_view(ticker, rows, close=close, as_of=as_of, price_bars=price_bars)
    stock = db.get(Stock, ticker)

    # 10yr return butuh >= ~9 tahun histori; tandai apakah span mencukupi.
    span = view.price_return_span_days
    is_10yr = span is not None and span >= 9 * 365

    return FundamentalsResponse(
        ticker=ticker,
        name=stock.name if stock else None,
        sector=stock.sector if stock else None,
        raw=RawOut(
            revenue_ttm=view.revenue_ttm,
            net_income_ttm=view.net_income_ttm,
            gross_profit=view.gross_profit,
            income_from_operations=view.income_from_operations,
            common_equity=view.common_equity,
            cash_equivalents=view.cash_equivalents,
            total_debt=view.total_debt,
            roe=view.roe,
            eps=view.eps,
            dps=view.dps,
        ),
        derived=DerivedOut(
            close=view.close,
            date=view.date,
            shares_outstanding=view.shares_outstanding,
            market_cap=view.market_cap,
            pe_annualised=view.pe_annualised,
            pbv=view.pbv,
            dividend_yield=view.dividend_yield,
        ),
        growth=GrowthOut(
            revenue_growth_yoy=view.revenue_growth_yoy,
            revenue_growth_3yr=view.revenue_growth_3yr,
            net_income_growth_yoy=view.net_income_growth_yoy,
            net_income_growth_3yr=view.net_income_growth_3yr,
            sales_growth_streak=view.sales_growth_streak,
        ),
        annual=[
            AnnualPointOut(period=a.period, revenue=a.revenue, net_income=a.net_income)
            for a in view.annual
        ],
        roe_5yr_avg=view.roe_5yr_avg,
        dividend_streak=view.dividend_streak,
        price_return=view.price_return,
        availability=AvailabilityOut(
            roe_5yr_avg=view.roe_5yr_avg is not None,
            dividend_streak=view.dividend_streak is not None,
            income_from_operations=view.income_from_operations is not None,
            price_return_is_10yr=is_10yr,
            price_return_span_days=span,
        ),
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()


@router.get("/{ticker}", response_model=FundamentalsResponse)
def get_fundamentals(
    ticker: str,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    ticker = ticker.strip().upper()
    cache_key = CACHE_KEY.format(ticker=ticker)

    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    rows = list(db.scalars(select(Fundamental).where(Fundamental.ticker == ticker)))
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Tidak ada data fundamental untuk '{ticker}'. Jalankan ingest fundamental dulu.",
        )

    payload = _build_payload(ticker, rows, db)
    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_REPORT)
    return payload
