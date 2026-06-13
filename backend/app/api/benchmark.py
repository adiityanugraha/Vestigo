"""Strategy Benchmark API (Phase 4, Day 6).

GET /api/benchmark
  Tabel metrik seluruh strategi tervalidasi berdampingan + baris pembanding
  pasar (IHSG buy-and-hold) + flag "mengalahkan pasar". Diurutkan CAGR menurun.

Query params:
  hold    : horizon holding (1/3/7/30, default 30)
  refresh : abaikan cache & hitung ulang
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.db.session import get_db
from app.quant import benchmark as bench
from app.quant import performance_metrics as pm

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

CACHE_KEY = "benchmark:hold={hold}"

DISCLAIMER = (
    "Perbandingan historis adalah alat bantu analisis/edukasi, BUKAN rekomendasi "
    "atau jaminan kinerja masa depan. Strategi memuat biaya 0,3% per trade & "
    "keterbatasan survivorship; IHSG dihitung buy-and-hold tanpa biaya."
)


class BenchmarkRow(BaseModel):
    strategy: str
    name: str | None = None
    is_benchmark: bool
    n_periods: int
    metrics: dict[str, float]
    beats_market_cagr: bool | None = None
    beats_market_sharpe: bool | None = None


class BenchmarkResponse(BaseModel):
    hold: int
    market: BenchmarkRow
    strategies: list[BenchmarkRow]
    methodology: str
    disclaimer: str
    cached: bool
    generated_at: str


def _round_metrics(row: dict) -> dict:
    row = dict(row)
    row["metrics"] = {k: round(v, 6) for k, v in row["metrics"].items()}
    return row


@router.get("", response_model=BenchmarkResponse)
def get_benchmark(
    hold: int = Query(pm.DEFAULT_HOLD),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    if hold not in (1, 3, 7, 30):
        raise HTTPException(status_code=422, detail="hold harus salah satu dari 1/3/7/30.")

    cache_key = CACHE_KEY.format(hold=hold)
    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    result = bench.compute_benchmark(db, hold=hold)
    payload = BenchmarkResponse(
        hold=hold,
        market=_round_metrics(result["market"]),
        strategies=[_round_metrics(r) for r in result["strategies"]],
        methodology=(
            f"Rebalancing kohort non-overlap {hold} hari, basket equal-weight, biaya "
            f"0,3%/trade; IHSG buy-and-hold tanpa biaya; anualisasi {pm.TRADING_DAYS} "
            f"hari bursa; Rf {pm.RISK_FREE_ANNUAL*100:.0f}%/tahun."
        ),
        disclaimer=DISCLAIMER,
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
