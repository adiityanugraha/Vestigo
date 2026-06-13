"""Risk Exposure (per strategi) API (Phase 4, Day 8).

GET /api/risk-profile/{strategy}
  Profil risiko satu strategi TERVALIDASI: volatility (anualisasi), avg ATR%,
  beta vs IHSG, max drawdown, losing streak + klasifikasi Low/Medium/High.
  Berbeda dari /api/risk/{ticker} (Phase 2, per-saham).

Query params:
  hold    : horizon holding (1/3/7/30, default 30)
  refresh : abaikan cache
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.db.session import get_db
from app.quant import performance_metrics as pm
from app.quant import risk_profile as rp

router = APIRouter(prefix="/api/risk-profile", tags=["risk-profile"])

CACHE_KEY = "risk-profile:{strategy}:hold={hold}"

DISCLAIMER = (
    "Profil risiko historis adalah alat bantu analisis/edukasi, BUKAN jaminan "
    "risiko masa depan. Klasifikasi berbasis volatilitas & drawdown periode uji."
)


class RiskProfileResponse(BaseModel):
    strategy: str
    name: str | None = None
    hold: int
    volatility: float
    avg_atr_pct: float | None
    beta: float
    max_drawdown: float
    losing_streak: int
    risk_level: str
    n_periods: int
    thresholds: dict[str, float]
    disclaimer: str
    cached: bool
    generated_at: str


@router.get("/{strategy}", response_model=RiskProfileResponse)
def get_risk_profile(
    strategy: str,
    hold: int = Query(pm.DEFAULT_HOLD),
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

    cache_key = CACHE_KEY.format(strategy=strategy, hold=hold)
    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    p = rp.compute_risk_profile(db, strategy, hold=hold)
    payload = RiskProfileResponse(
        strategy=strategy,
        name=p["name"],
        hold=hold,
        volatility=round(p["volatility"], 6),
        avg_atr_pct=round(p["avg_atr_pct"], 6) if p["avg_atr_pct"] is not None else None,
        beta=round(p["beta"], 4),
        max_drawdown=round(p["max_drawdown"], 6),
        losing_streak=p["losing_streak"],
        risk_level=p["risk_level"],
        n_periods=p["n_periods"],
        thresholds={
            "vol_high": rp.VOL_HIGH,
            "vol_low": rp.VOL_LOW,
            "dd_high": rp.DD_HIGH,
            "dd_low": rp.DD_LOW,
        },
        disclaimer=DISCLAIMER,
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
