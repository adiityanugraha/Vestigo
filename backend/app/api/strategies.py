"""Strategies API (Phase 3 Day 3).

GET /api/strategies
  Daftar semua strategi screening yang terdaftar di Strategy Registry
  (key, nama, tipe technical/fundamental, label output). Dipakai frontend
  untuk membangun pemilih strategi (Day 14).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.strategies import registry

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyMetaOut(BaseModel):
    key: str
    name: str
    type: str  # technical | fundamental
    output_label: str


@router.get("", response_model=list[StrategyMetaOut])
def list_strategies() -> list[dict]:
    return [strategy.describe() for strategy in registry.all_strategies()]
