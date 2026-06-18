"""Portfolio AI Advisor API (Phase 5 Day 11).

POST /api/portfolio-advisor
  Body: {risk, capital?, universe?}. Alokasi dari Portfolio Builder (Phase 4) +
  penjelasan LLM kenapa tiap bobot. Disclaimer WAJIB (bukan nasihat keuangan).
  422 bila input/hasil invalid. Di-cache di Redis (build portfolio cukup berat).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai import portfolio_advisor
from app.cache import redis_client
from app.db.session import get_db

router = APIRouter(prefix="/api/portfolio-advisor", tags=["portfolio-advisor"])

CACHE_KEY = "portfolio-advisor:{risk}:{capital}:{universe}"


class AdvisorRequest(BaseModel):
    risk: str = Field(..., description="CONSERVATIVE | MODERATE | AGGRESSIVE")
    capital: float = Field(100_000_000, gt=0)
    universe: str = Field("lq45", description="all | lq45 | screened")


class AdvisorResponse(BaseModel):
    risk_profile: str
    capital: float
    universe: str
    n_positions: int
    allocations: list[dict]
    summary: dict
    explanation: str | None = None
    disclaimer: str
    cached: bool = False
    generated_at: str | None = None


@router.post("", response_model=AdvisorResponse)
def post_portfolio_advisor(body: AdvisorRequest, db: Session = Depends(get_db)) -> dict:
    cache_key = CACHE_KEY.format(
        risk=body.risk.strip().upper(), capital=body.capital, universe=body.universe.strip().lower()
    )
    cached = redis_client.cache_get_json(cache_key)
    if cached is not None:
        cached["cached"] = True
        return cached

    try:
        result = portfolio_advisor.advise(body.risk, body.capital, body.universe, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload = AdvisorResponse(
        risk_profile=result["risk_profile"],
        capital=result["capital"],
        universe=result["universe"],
        n_positions=result["n_positions"],
        allocations=result["allocations"],
        summary=result["summary"],
        explanation=result.get("explanation"),
        disclaimer=result.get("disclaimer", ""),
        cached=False,
        generated_at=result.get("generated_at"),
    ).model_dump()

    redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_QUANT)
    return payload
