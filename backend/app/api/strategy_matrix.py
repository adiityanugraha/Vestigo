"""Strategy Comparison Dashboard API (Phase 3 Day 8).

GET /api/strategy-matrix
  Matriks saham x strategi dari strategy_results tanggal terbaru. Tiap sel:
  true (lolos) / false (gagal) / null (tak dinilai). Hasil di-cache di Redis
  (sering diakses dashboard).

Query params:
  min_passed : hanya tampilkan saham yang lolos minimal N strategi (default 1).
  refresh    : abaikan cache & hitung ulang (default false).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.core import strategy_matrix
from app.db.session import get_db

router = APIRouter(prefix="/api/strategy-matrix", tags=["strategy-matrix"])

CACHE_KEY = "strategy-matrix:min_passed={min_passed}"


class StrategyColumnOut(BaseModel):
    key: str
    name: str
    type: str
    output_label: str


class MatrixRowOut(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    results: dict[str, bool | None]
    passed_count: int
    passed_strategies: list[str]


class StrategyMatrixResponse(BaseModel):
    date: str | None
    generated_at: str
    cached: bool
    universe_evaluated: int
    strategies: list[StrategyColumnOut]
    matrix: list[MatrixRowOut]


@router.get("", response_model=StrategyMatrixResponse)
def get_strategy_matrix(
    min_passed: int = Query(1, ge=0, le=9),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    cache_key = CACHE_KEY.format(min_passed=min_passed)
    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    result = strategy_matrix.build_strategy_matrix(db, min_passed=min_passed)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    result["cached"] = False
    redis_client.cache_set_json(cache_key, result, ttl=redis_client.TTL_RANKING)
    return result
