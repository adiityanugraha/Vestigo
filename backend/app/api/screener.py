"""Screener API — port server-side dari predictionPipeline.ts (Phase 1).

GET /api/screener
  Muat bar harian per ticker dari market_data -> jalankan screener (BSJP/BPJS)
  -> prediksi ML -> ranking (predictionScore = probabilityUp*100 + score)
  -> kembalikan top-N per strategi. Hasil di-cache di Redis (TTL_RANKING).

Query params:
  limit       : jumlah kandidat per strategi (default 5)
  use_ml      : sertakan skor ML (default true)
  refresh     : abaikan cache & hitung ulang (default false)
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.core import screener as screener_core
from app.core.instruments import is_index
from app.db.models import MarketData, ScreeningHistory, Stock
from app.db.session import get_db
from app.ml import inference
from app.ml.features import build_feature_vector

router = APIRouter(prefix="/api/screener", tags=["screener"])

CACHE_KEY = "screener:result:limit={limit}:ml={ml}"


# --------------------------------------------------------------------------- #
# Response schema
# --------------------------------------------------------------------------- #
class PredictionOut(BaseModel):
    label: int
    probability_up: float
    probability_down: float


class LevelsOut(BaseModel):
    entry: float
    stop_loss: float
    take_profit: float
    exit: float
    risk_per_share: float
    reward_per_share: float


class IndicatorsOut(BaseModel):
    price_ma5: float | None = None
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    vwap: float | None = None
    atr: float | None = None
    volume_spike_ratio: float | None = None


class CandidateOut(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    date: str
    open: float
    close: float
    volume: float
    value: float
    strategy: str
    score: float
    prediction_score: float
    criteria: dict[str, bool]
    prediction: PredictionOut | None = None
    levels: LevelsOut
    indicators: IndicatorsOut


class ScreenerResponse(BaseModel):
    generated_at: str
    universe: int
    screened: int
    persisted: int = 0
    cached: bool
    bsjp: list[CandidateOut]
    bpjs: list[CandidateOut]


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def _load_bars_by_ticker(db: Session) -> dict[str, list[MarketData]]:
    """Semua bar market_data dikelompokkan per ticker, urut kronologis."""
    rows = db.scalars(
        select(MarketData).order_by(MarketData.ticker, MarketData.date)
    )
    grouped: dict[str, list[MarketData]] = {}
    for row in rows:
        grouped.setdefault(row.ticker, []).append(row)
    return grouped


def _candidate_to_dict(
    candidate: screener_core.ScreenerCandidate,
    bars: list[MarketData],
    prediction: inference.Prediction | None,
    stock: Stock | None,
) -> dict:
    inp = candidate.inp
    latest = bars[-1]
    prediction_up = prediction.probability_up if prediction else 0.0

    return CandidateOut(
        ticker=candidate.ticker,
        name=stock.name if stock else None,
        sector=stock.sector if stock else None,
        date=latest.date.isoformat(),
        open=inp.current_open,
        close=inp.current_close,
        volume=inp.current_volume,
        value=candidate.value,
        strategy=candidate.strategy,
        score=candidate.score,
        prediction_score=prediction_up * 100 + candidate.score,
        criteria=candidate.criteria,
        prediction=(
            PredictionOut(
                label=prediction.label,
                probability_up=prediction.probability_up,
                probability_down=prediction.probability_down,
            )
            if prediction
            else None
        ),
        levels=LevelsOut(
            entry=candidate.levels.entry,
            stop_loss=candidate.levels.stop_loss,
            take_profit=candidate.levels.take_profit,
            exit=candidate.levels.exit,
            risk_per_share=candidate.levels.risk_per_share,
            reward_per_share=candidate.levels.reward_per_share,
        ),
        indicators=IndicatorsOut(
            price_ma5=inp.price_ma5,
            rsi=inp.rsi,
            macd=inp.macd,
            macd_signal=inp.macd_signal,
            macd_histogram=inp.macd_histogram,
            bb_upper=inp.bb_upper,
            bb_middle=inp.bb_middle,
            bb_lower=inp.bb_lower,
            vwap=inp.vwap,
            atr=inp.atr,
            volume_spike_ratio=inp.volume_spike_ratio,
        ),
    ).model_dump()


def _predict(bars: list[MarketData]) -> inference.Prediction | None:
    feature_vector = build_feature_vector(bars)
    if feature_vector is None:
        return None
    try:
        return inference.predict_from_features(feature_vector)
    except Exception:  # noqa: BLE001 — ML opsional; screener tetap jalan tanpa prediksi
        return None


def _persist_screening_history(db: Session, candidates: list[dict]) -> int:
    """Simpan seluruh kandidat yang lolos screener ke screening_history.

    Idempoten: upsert per (date, ticker, strategy). Skor yang disimpan adalah
    skor screener (bukan predictionScore) sesuai skema blueprint. Dipakai Day 12
    (riwayat & performance tracking).
    """
    if not candidates:
        return 0

    rows = [
        {
            "date": date_cls.fromisoformat(candidate["date"]),
            "ticker": candidate["ticker"],
            "score": candidate["score"],
            "strategy": candidate["strategy"],
        }
        for candidate in candidates
    ]
    stmt = pg_insert(ScreeningHistory).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_screening_date_ticker_strategy",
        set_={"score": stmt.excluded.score},
    )
    db.execute(stmt)
    db.commit()
    return len(rows)


def run_screener(db: Session, limit: int, use_ml: bool) -> dict:
    bars_by_ticker = _load_bars_by_ticker(db)
    stock_map = {stock.ticker: stock for stock in db.scalars(select(Stock))}

    all_candidates: list[dict] = []
    for ticker, bars in bars_by_ticker.items():
        if is_index(ticker):  # indeks bukan saham tradable -> dikecualikan
            continue
        candidates = screener_core.screen_bars(ticker, bars)
        if not candidates:
            continue
        prediction = _predict(bars) if use_ml else None
        for candidate in candidates:
            all_candidates.append(
                _candidate_to_dict(candidate, bars, prediction, stock_map.get(ticker))
            )

    # Persist hasil harian (semua yang lolos, bukan hanya top-N) untuk Day 12.
    _persist_screening_history(db, all_candidates)

    def top(strategy: str) -> list[dict]:
        items = [c for c in all_candidates if c["strategy"] == strategy]
        items.sort(key=lambda c: c["prediction_score"], reverse=True)
        return items[:limit]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "universe": len(bars_by_ticker),
        "screened": len(all_candidates),
        "persisted": len(all_candidates),
        "cached": False,
        "bsjp": top("BSJP"),
        "bpjs": top("BPJS"),
    }


@router.get("", response_model=ScreenerResponse)
def get_screener(
    limit: int = Query(5, ge=1, le=50),
    use_ml: bool = Query(True),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    cache_key = CACHE_KEY.format(limit=limit, ml=use_ml)

    if not refresh:
        cached = redis_client.cache_get_json(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

    result = run_screener(db, limit=limit, use_ml=use_ml)
    redis_client.cache_set_json(cache_key, result, ttl=redis_client.TTL_RANKING)
    return result
