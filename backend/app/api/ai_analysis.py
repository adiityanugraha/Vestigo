"""AI Analyst Engine API (Phase 5 Day 5).

GET /api/ai-analysis/{ticker}
  Narasi AI ter-grounding sebuah saham: summary, bullish factors, risk factors,
  confidence (= Composite Score sistem). Angka dari tool Phase 1-4, LLM hanya
  menarasikan. Hasil disimpan ke tabel ai_reports (upsert per date+ticker) &
  di-cache di Redis (di-pra-generate oleh job malam Day 14).

Query params:
  refresh : abaikan cache & hasilkan ulang (default false)
"""

from __future__ import annotations

from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.ai import ai_analysis
from app.cache import redis_client
from app.db.models import AiReport
from app.db.session import get_db

router = APIRouter(prefix="/api/ai-analysis", tags=["ai-analysis"])

CACHE_KEY = "ai-analysis:{ticker}"


class AiAnalysisResponse(BaseModel):
    ticker: str
    date: str | None = None
    confidence: float | None = None
    summary: str | None = None
    bullish_factors: list[str] = []
    risk_factors: list[str] = []
    ai_generated: bool = False
    note: str | None = None
    disclaimer: str
    cached: bool = False
    generated_at: str | None = None


def _persist(db: Session, result: dict) -> None:
    """Upsert hasil analisis ke ai_reports (hanya bila ada tanggal & narasi)."""
    if not result.get("date") or not result.get("ai_generated"):
        return
    stmt = pg_insert(AiReport).values(
        date=date_cls.fromisoformat(result["date"]),
        ticker=result["ticker"],
        summary=result.get("summary"),
        bullish_factors=result.get("bullish_factors", []),
        risk_factors=result.get("risk_factors", []),
        confidence=result.get("confidence"),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["date", "ticker"],
        set_={
            "summary": stmt.excluded.summary,
            "bullish_factors": stmt.excluded.bullish_factors,
            "risk_factors": stmt.excluded.risk_factors,
            "confidence": stmt.excluded.confidence,
            "updated_at": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()


@router.get("/{ticker}", response_model=AiAnalysisResponse)
def get_ai_analysis(
    ticker: str,
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    ticker = ticker.strip().upper()
    cache_key = CACHE_KEY.format(ticker=ticker)

    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    result = ai_analysis.analyze(ticker)
    # Gagal total (mis. tidak ada market_data sama sekali) -> 404.
    if "error" in result and not result.get("date"):
        raise HTTPException(status_code=404, detail=result["error"])

    _persist(db, result)

    # Bila narasi LLM gagal (ada 'error' tapi data tetap ada), sampaikan via note.
    note = result.get("note") or result.get("error")
    payload = AiAnalysisResponse(
        ticker=result["ticker"],
        date=result.get("date"),
        confidence=result.get("confidence"),
        summary=result.get("summary"),
        bullish_factors=result.get("bullish_factors", []),
        risk_factors=result.get("risk_factors", []),
        ai_generated=result.get("ai_generated", False),
        note=note,
        disclaimer=result.get("disclaimer", ""),
        cached=False,
        generated_at=result.get("generated_at"),
    ).model_dump()

    # Cache hanya bila narasi AI berhasil (jangan cache state "AI off").
    if payload["ai_generated"]:
        redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_REPORT)
    return payload
