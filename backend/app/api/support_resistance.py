"""Support & Resistance API (Day 10).

GET /api/support-resistance/{ticker}
  Rakit OHLC + ATR dari market_data -> hitung Support/Resistance + Breakout Zone
  (app.core.sr_engine) lewat Swing High/Low, Pivot Point, ATR Band. Sering
  diakses -> hasil di-cache di Redis (TTL_SUPPORT_RESISTANCE).

Query params:
  refresh : abaikan cache & hitung ulang (default false)
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.core import sr_engine
from app.db.models import MarketData, Stock
from app.db.session import get_db

router = APIRouter(prefix="/api/support-resistance", tags=["support-resistance"])

CACHE_KEY = "support-resistance:{ticker}"

# Minimal bar agar swing point bisa terbentuk (butuh window kiri+kanan).
MIN_BARS = 10


# --------------------------------------------------------------------------- #
# Response schema
# --------------------------------------------------------------------------- #
class ZoneOut(BaseModel):
    lower: float
    upper: float


class PivotOut(BaseModel):
    pivot: float
    r1: float
    r2: float
    s1: float
    s2: float


class MethodsOut(BaseModel):
    pivot: PivotOut
    swing_high: float | None = None
    swing_low: float | None = None
    atr_band: ZoneOut | None = None


class SRResponse(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    date: str
    current: float
    support: float | None = None
    resistance: float | None = None
    breakout_zone: ZoneOut | None = None
    methods: MethodsOut
    cached: bool
    generated_at: str


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def _load_bars(db: Session, ticker: str) -> list[MarketData]:
    return list(
        db.scalars(
            select(MarketData)
            .where(MarketData.ticker == ticker)
            .order_by(MarketData.date)
        )
    )


def build_sr_input(bars: list[MarketData]) -> sr_engine.SRInput:
    highs = [float(bar.high) for bar in bars if bar.high is not None]
    lows = [float(bar.low) for bar in bars if bar.low is not None]
    closes = [float(bar.close) for bar in bars if bar.close is not None]
    return sr_engine.SRInput(highs=highs, lows=lows, closes=closes, atr=bars[-1].atr)


def _zone_out(zone: sr_engine.Zone | None) -> ZoneOut | None:
    return None if zone is None else ZoneOut(lower=zone.lower, upper=zone.upper)


@router.get("/{ticker}", response_model=SRResponse)
def get_support_resistance(
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

    bars = _load_bars(db, ticker)
    if not bars:
        raise HTTPException(
            status_code=404,
            detail=f"Tidak ada market_data untuk ticker '{ticker}'.",
        )
    if len(bars) < MIN_BARS:
        raise HTTPException(
            status_code=422,
            detail=f"Data '{ticker}' belum cukup ({len(bars)} bar, minimal {MIN_BARS}).",
        )

    result = sr_engine.compute_sr(build_sr_input(bars))

    stock = db.get(Stock, ticker)
    latest = bars[-1]
    payload = SRResponse(
        ticker=ticker,
        name=stock.name if stock else None,
        sector=stock.sector if stock else None,
        date=latest.date.isoformat(),
        current=result.current,
        support=result.support,
        resistance=result.resistance,
        breakout_zone=_zone_out(result.breakout_zone),
        methods=MethodsOut(
            pivot=PivotOut(
                pivot=result.pivot.pivot,
                r1=result.pivot.r1,
                r2=result.pivot.r2,
                s1=result.pivot.s1,
                s2=result.pivot.s2,
            ),
            swing_high=result.swing_high,
            swing_low=result.swing_low,
            atr_band=_zone_out(result.atr_band),
        ),
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_SUPPORT_RESISTANCE)
    return payload
