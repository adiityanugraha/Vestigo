"""Equity Curve API (Phase 4, Day 5).

GET /api/equity-curve/{strategy}
  Kurva pertumbuhan modal (ternormalisasi) + peak + drawdown per titik untuk
  satu strategi TERVALIDASI (5 teknikal). Konsisten dengan /api/performance
  (seri return kohort yang sama). Disimpan ke equity_curve & di-cache.

Query params:
  hold            : horizon holding (1/3/7/30, default 30)
  initial_capital : skala nominal untuk tampilan (default 100.000.000 rupiah)
  refresh         : abaikan cache & hitung ulang
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.db.session import get_db
from app.quant import equity_curve as ec
from app.quant import performance_metrics as pm

router = APIRouter(prefix="/api/equity-curve", tags=["equity-curve"])

CACHE_KEY = "equity-curve:{strategy}:hold={hold}:cap={cap}"

DISCLAIMER = (
    "Equity curve historis adalah alat bantu analisis/edukasi, BUKAN jaminan "
    "kinerja masa depan. Mengandung asumsi biaya 0,3% per trade & keterbatasan "
    "survivorship (hanya saham yang masih listing)."
)


class EquityPoint(BaseModel):
    date: str
    value: float
    peak: float
    drawdown: float


class EquityCurveResponse(BaseModel):
    strategy: str
    name: str | None = None
    hold: int
    initial_capital: float
    points: list[EquityPoint]
    summary: dict[str, float]
    methodology: str
    disclaimer: str
    cached: bool
    generated_at: str


@router.get("/{strategy}", response_model=EquityCurveResponse)
def get_equity_curve(
    strategy: str,
    hold: int = Query(pm.DEFAULT_HOLD),
    initial_capital: float = Query(100_000_000.0, gt=0),
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

    cache_key = CACHE_KEY.format(strategy=strategy, hold=hold, cap=int(initial_capital))
    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    points = ec.build_curve(db, strategy, hold=hold)
    if hold == pm.DEFAULT_HOLD:
        ec.persist_curve(db, strategy, points)  # tabel simpan versi ternormalisasi

    summary = ec.curve_summary(points)
    payload = EquityCurveResponse(
        strategy=strategy,
        name=pm.strategy_display_name(strategy),
        hold=hold,
        initial_capital=initial_capital,
        points=[
            EquityPoint(
                date=p["date"].isoformat(),
                value=round(p["portfolio_value"] * initial_capital, 2),
                peak=round(p["peak"] * initial_capital, 2),
                drawdown=round(p["drawdown"], 6),
            )
            for p in points
        ],
        summary={
            "final_value": round(summary["final_value"] * initial_capital, 2),
            "total_return": round(summary["total_return"], 6),
            "max_drawdown": round(summary["max_drawdown"], 6),
        },
        methodology=(
            f"Rebalancing kohort non-overlap {hold} hari bursa, basket equal-weight; "
            f"nilai ternormalisasi diskalakan ke modal awal Rp {initial_capital:,.0f}."
        ),
        disclaimer=DISCLAIMER,
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
