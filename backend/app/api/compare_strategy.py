"""AI Strategy Comparator API (Phase 5 Day 10).

GET /api/compare-strategy?a=&b=
  Bandingkan dua strategi teknikal tervalidasi (Phase 4) + narasi tradeoff LLM.
  Angka dari strategy_performance. Hasil disimpan ke strategy_comparisons (upsert
  per pasangan) & di-cache di Redis. 422 bila pasangan invalid (mis. strategi
  fundamental / sama / tak dikenal).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.ai import strategy_comparator
from app.cache import redis_client
from app.db.models import StrategyComparison
from app.db.session import get_db

router = APIRouter(prefix="/api/compare-strategy", tags=["compare-strategy"])

CACHE_KEY = "compare-strategy:{a}:{b}"


class CompareResponse(BaseModel):
    strategy_a: str
    strategy_b: str
    name_a: str | None = None
    name_b: str | None = None
    metrics_a: dict[str, float] = {}
    metrics_b: dict[str, float] = {}
    comparison: str | None = None
    disclaimer: str
    cached: bool = False
    generated_at: str | None = None


def _persist(db: Session, result: dict) -> None:
    stmt = pg_insert(StrategyComparison).values(
        strategy_a=result["strategy_a"],
        strategy_b=result["strategy_b"],
        comparison=result.get("comparison"),
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_strategy_comparisons_pair",
        set_={"comparison": stmt.excluded.comparison, "updated_at": func.now()},
    )
    db.execute(stmt)
    db.commit()


@router.get("", response_model=CompareResponse)
def get_compare_strategy(
    a: str = Query(..., description="Strategi pertama (mis. breakout)."),
    b: str = Query(..., description="Strategi kedua (mis. trend_following)."),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    key_a, key_b = a.strip().lower(), b.strip().lower()
    cache_key = CACHE_KEY.format(a=key_a, b=key_b)

    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    try:
        result = strategy_comparator.compare(key_a, key_b, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    _persist(db, result)

    payload = CompareResponse(
        strategy_a=result["strategy_a"],
        strategy_b=result["strategy_b"],
        name_a=result.get("name_a"),
        name_b=result.get("name_b"),
        metrics_a=result.get("metrics_a", {}),
        metrics_b=result.get("metrics_b", {}),
        comparison=result.get("comparison"),
        disclaimer=result.get("disclaimer", ""),
        cached=False,
        generated_at=result.get("generated_at"),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
