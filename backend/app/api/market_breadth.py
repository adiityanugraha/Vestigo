"""Market Breadth API (Day 11).

GET /api/market-breadth
  Hitung breadth pasar untuk satu hari (default: tanggal terbaru di market_data):
  advancers/decliners, Bullish Ratio, Top Gainers/Losers, Sector Performance
  (app.core.market_breadth). Hasil disimpan ke PostgreSQL (tabel market_breadth,
  upsert per tanggal) dan di-cache di Redis.

Query params:
  date     : YYYY-MM-DD (default: tanggal terbaru yang tersedia)
  top      : jumlah top gainers/losers (default 5)
  persist  : simpan hasil ke PostgreSQL (default true)
  refresh  : abaikan cache & hitung ulang (default false)
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.core import market_breadth as mb
from app.core.instruments import is_index
from app.db.models import MarketBreadth, MarketData, Stock
from app.db.queries import load_recent_bars_by_ticker
from app.db.session import get_db

router = APIRouter(prefix="/api/market-breadth", tags=["market-breadth"])

CACHE_KEY = "market-breadth:{date}:top={top}"

# Breadth hanya butuh bar `target` + bar tepat sebelumnya. 20 hari kalender
# pasti memuat ≥2 bar bursa (cukup walau ada libur), tanpa memuat seluruh tabel.
BREADTH_LOOKBACK_DAYS = 20


# --------------------------------------------------------------------------- #
# Response schema
# --------------------------------------------------------------------------- #
class MoverOut(BaseModel):
    ticker: str
    name: str | None = None
    close: float
    change_pct: float


class SectorOut(BaseModel):
    sector: str
    avg_change_pct: float
    count: int


class BreadthResponse(BaseModel):
    date: str
    advancers: int
    decliners: int
    unchanged: int
    total: int
    bullish_ratio: float | None = None
    top_gainers: list[MoverOut]
    top_losers: list[MoverOut]
    sector_performance: list[SectorOut]
    persisted: bool
    cached: bool
    generated_at: str


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def _resolve_date(db: Session, date_param: str | None) -> date_cls:
    if date_param:
        try:
            return date_cls.fromisoformat(date_param)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Format date harus YYYY-MM-DD.") from exc
    latest = db.scalar(select(func.max(MarketData.date)))
    if latest is None:
        raise HTTPException(status_code=404, detail="market_data masih kosong.")
    return latest


def _build_changes(db: Session, target: date_cls) -> list[mb.StockChange]:
    """Perubahan harian tiap saham pada `target` = close vs bar tepat sebelumnya."""
    by_ticker = load_recent_bars_by_ticker(
        db, lookback_days=BREADTH_LOOKBACK_DAYS, as_of=target
    )

    stock_map = {stock.ticker: stock for stock in db.scalars(select(Stock))}

    changes: list[mb.StockChange] = []
    for ticker, bars in by_ticker.items():
        if is_index(ticker):  # indeks tidak dihitung di breadth saham
            continue
        # Cari bar pada tanggal target + bar tepat sebelumnya.
        idx = next((i for i, b in enumerate(bars) if b.date == target), None)
        if idx is None or idx == 0:
            continue
        current = bars[idx]
        previous = bars[idx - 1]
        if not current.close or not previous.close:
            continue
        change_pct = current.close / previous.close - 1
        stock = stock_map.get(ticker)
        changes.append(
            mb.StockChange(
                ticker=ticker,
                name=stock.name if stock else None,
                sector=stock.sector if stock else None,
                close=float(current.close),
                change_pct=change_pct,
            )
        )
    return changes


def _persist(db: Session, result: mb.BreadthResult) -> None:
    stmt = pg_insert(MarketBreadth).values(
        date=date_cls.fromisoformat(result.date),
        advancers=result.advancers,
        decliners=result.decliners,
        unchanged=result.unchanged,
        total=result.total,
        bullish_ratio=result.bullish_ratio,
        top_gainers=result.top_gainers,
        top_losers=result.top_losers,
        sector_performance=result.sector_performance,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],
        set_={
            "advancers": stmt.excluded.advancers,
            "decliners": stmt.excluded.decliners,
            "unchanged": stmt.excluded.unchanged,
            "total": stmt.excluded.total,
            "bullish_ratio": stmt.excluded.bullish_ratio,
            "top_gainers": stmt.excluded.top_gainers,
            "top_losers": stmt.excluded.top_losers,
            "sector_performance": stmt.excluded.sector_performance,
        },
    )
    db.execute(stmt)
    db.commit()


@router.get("", response_model=BreadthResponse)
def get_market_breadth(
    date: str | None = Query(None),
    top: int = Query(mb.DEFAULT_TOP_N, ge=1, le=20),
    persist: bool = Query(True),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    target = _resolve_date(db, date)
    cache_key = CACHE_KEY.format(date=target.isoformat(), top=top)

    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    changes = _build_changes(db, target)
    if not changes:
        raise HTTPException(
            status_code=404,
            detail=f"Tidak ada perubahan harian yang bisa dihitung untuk {target.isoformat()}.",
        )

    result = mb.compute_breadth(changes, date=target.isoformat(), top_n=top)

    persisted = False
    if persist:
        _persist(db, result)
        persisted = True

    payload = BreadthResponse(
        date=result.date,
        advancers=result.advancers,
        decliners=result.decliners,
        unchanged=result.unchanged,
        total=result.total,
        bullish_ratio=result.bullish_ratio,
        top_gainers=[MoverOut(**g) for g in result.top_gainers],
        top_losers=[MoverOut(**g) for g in result.top_losers],
        sector_performance=[SectorOut(**s) for s in result.sector_performance],
        persisted=persisted,
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_RANKING)
    return payload
