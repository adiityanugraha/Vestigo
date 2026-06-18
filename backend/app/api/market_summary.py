"""Market Narrator API (Phase 5 Day 12).

GET /api/market-summary
  Narasi kondisi pasar harian (breadth + rotasi sektor + benchmark strategi).
  Angka dari sistem; LLM menarasikan. Disimpan ke market_narratives (upsert per
  tanggal) & di-cache di Redis. Query: refresh.
"""

from __future__ import annotations

from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.ai import market_narrator
from app.cache import redis_client
from app.db.models import MarketNarrative
from app.db.session import get_db

router = APIRouter(prefix="/api/market-summary", tags=["market-summary"])

CACHE_KEY = "market-summary:{date}"


class MarketSummaryResponse(BaseModel):
    date: str | None = None
    summary: str | None = None
    bullish_ratio: float | None = None
    advancers: int | None = None
    decliners: int | None = None
    leading_sectors: list[str] = []
    lagging_sectors: list[str] = []
    best_strategy: str | None = None
    disclaimer: str
    cached: bool = False
    generated_at: str | None = None


def _persist(db: Session, result: dict) -> None:
    if not result.get("date"):
        return
    stmt = pg_insert(MarketNarrative).values(
        date=date_cls.fromisoformat(result["date"]), summary=result.get("summary")
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["date"],
        set_={"summary": stmt.excluded.summary, "updated_at": func.now()},
    )
    db.execute(stmt)
    db.commit()


@router.get("", response_model=MarketSummaryResponse)
def get_market_summary(refresh: bool = Query(False), db: Session = Depends(get_db)) -> dict:
    # Cache key per tanggal terbaru market_data (lewat hasil narator).
    result = None
    if not refresh:
        # Coba cache "terbaru" tanpa tahu tanggalnya: pakai key sentinel harian.
        cached = redis_client.cache_get_json(CACHE_KEY.format(date="latest"))
        if cached is not None:
            cached["cached"] = True
            return cached

    result = market_narrator.summarize(db)
    if not result.get("date"):
        raise HTTPException(status_code=404, detail="Data pasar belum tersedia.")

    _persist(db, result)

    payload = MarketSummaryResponse(
        date=result.get("date"),
        summary=result.get("summary"),
        bullish_ratio=result.get("bullish_ratio"),
        advancers=result.get("advancers"),
        decliners=result.get("decliners"),
        leading_sectors=result.get("leading_sectors", []),
        lagging_sectors=result.get("lagging_sectors", []),
        best_strategy=result.get("best_strategy"),
        disclaimer=result.get("disclaimer", ""),
        cached=False,
        generated_at=result.get("generated_at"),
    ).model_dump()

    redis_client.cache_set_json(CACHE_KEY.format(date="latest"), payload, ttl=redis_client.TTL_REPORT)
    return payload
