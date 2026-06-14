"""Walk-Forward Backtesting API (Phase 4, Day 11).

GET /api/walkforward/{strategy}
  Uji stabilitas out-of-sample per tahun (anchored) + ringkasan konsistensi.
  Hanya strategi TERVALIDASI (5 teknikal).

Query params:
  hold            : horizon holding seri sumber (1/3/7/30, default 30)
  min_train_years : tahun awal sebagai train sebelum fold test (1..5, default 1)
  refresh         : abaikan cache
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.db.session import get_db
from app.quant import performance_metrics as pm
from app.quant import walk_forward as wf

router = APIRouter(prefix="/api/walkforward", tags=["walkforward"])

CACHE_KEY = "walkforward:{strategy}:hold={hold}:train={train}"

DISCLAIMER = (
    "Walk-forward menguji konsistensi historis (alat bantu analisis/edukasi), "
    "BUKAN jaminan kinerja masa depan. Strategi memuat biaya 0,3% per trade & "
    "keterbatasan survivorship."
)


class WalkForwardResponse(BaseModel):
    strategy: str
    name: str | None = None
    hold: int
    mode: str
    min_train_years: int
    folds: list[dict]
    out_of_sample: dict
    disclaimer: str
    cached: bool
    generated_at: str


@router.get("/{strategy}", response_model=WalkForwardResponse)
def get_walkforward(
    strategy: str,
    hold: int = Query(pm.DEFAULT_HOLD),
    min_train_years: int = Query(wf.DEFAULT_MIN_TRAIN_YEARS, ge=1, le=5),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    strategy = strategy.strip().lower()
    if strategy not in pm.VALIDATED_STRATEGIES:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Strategi '{strategy}' tidak divalidasi historis. Hanya strategi "
                f"teknikal: {', '.join(pm.VALIDATED_STRATEGIES)}."
            ),
        )
    if hold not in (1, 3, 7, 30):
        raise HTTPException(status_code=422, detail="hold harus salah satu dari 1/3/7/30.")

    cache_key = CACHE_KEY.format(strategy=strategy, hold=hold, train=min_train_years)
    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    result = wf.walk_forward(db, strategy, hold=hold, min_train_years=min_train_years)
    if not result["folds"]:
        raise HTTPException(
            status_code=422,
            detail=f"Histori '{strategy}' tak cukup untuk {min_train_years}+1 tahun fold.",
        )

    payload = WalkForwardResponse(
        strategy=result["strategy"],
        name=result["name"],
        hold=result["hold"],
        mode=result["mode"],
        min_train_years=result["min_train_years"],
        folds=result["folds"],
        out_of_sample=result["out_of_sample"],
        disclaimer=DISCLAIMER,
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
