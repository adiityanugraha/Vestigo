"""Correlation Matrix API (Phase 4, Day 9).

GET /api/correlation
  Matriks korelasi Pearson return harian atas universe terbatas (default LQ45)
  untuk membantu diversifikasi. Mengembalikan daftar ticker + matriks simetris
  (untuk heatmap) + pasangan paling berkorelasi. Pasangan unik disimpan ke
  correlation_matrix; respons di-cache.

Query params:
  universe : all | lq45 | screened (default lq45)
  window   : jumlah hari bursa untuk korelasi (default 90, 20..250)
  refresh  : abaikan cache
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.db.session import get_db
from app.quant import correlation_matrix as cm

router = APIRouter(prefix="/api/correlation", tags=["correlation"])

CACHE_KEY = "correlation:{universe}:{window}"

DISCLAIMER = (
    "Korelasi historis (alat bantu diversifikasi) dapat berubah, terutama saat "
    "pasar tertekan ketika korelasi cenderung naik. Bukan jaminan masa depan."
)


class CorrelationResponse(BaseModel):
    universe: str
    window: str
    tickers: list[str]
    matrix: list[list[float]]
    top_correlated: list[dict]
    n: int
    disclaimer: str
    computed_at: str
    cached: bool


@router.get("", response_model=CorrelationResponse)
def get_correlation(
    universe: str = Query("lq45"),
    window: int = Query(cm.DEFAULT_WINDOW, ge=20, le=250),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    universe = universe.strip().lower()
    if universe not in ("all", "lq45", "screened"):
        raise HTTPException(status_code=422, detail="universe harus all|lq45|screened.")

    cache_key = CACHE_KEY.format(universe=universe, window=window)
    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    result = cm.compute_correlation(db, universe=universe, window=window)
    payload = CorrelationResponse(
        universe=result["universe"],
        window=result["window"],
        tickers=result["tickers"],
        matrix=result["matrix"],
        top_correlated=[
            {"ticker_a": p["ticker_a"], "ticker_b": p["ticker_b"],
             "correlation": round(p["correlation"], 4)}
            for p in cm.top_correlated(result["pairs"], 15)
        ],
        n=len(result["tickers"]),
        disclaimer=DISCLAIMER,
        computed_at=result["computed_at"],
        cached=False,
    ).model_dump()

    # Jangan cache hasil degenerate (universe kosong / data kurang) agar tak
    # menyajikan matriks kosong basi saat data sudah tersedia.
    if payload["n"] >= 2:
        redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
