"""Job harian scheduler (Day 13).

Tiap job membuka sesi DB sendiri (tidak memakai dependency request) dan, bila
relevan, menghangatkan cache Redis sehingga endpoint melayani hasil instan.
Job didaftarkan ke APScheduler di app.scheduler.scheduler.

Dipakai juga sebagai fungsi biasa (mis. saat testing / pemicuan manual).
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.api import forecast as forecast_api
from app.api import stock_report
from app.api import strength as strength_api
from app.api.ranking import CACHE_KEY as RANKING_CACHE_KEY
from app.api.ranking import run_ranking
from app.api.screener import run_screener
from app.cache import redis_client
from app.core import market_data as md
from app.core import strategy_screener
from app.core.instruments import is_index
from app.core.strength_engine import DEFAULT_FULL_POINTS, DEFAULT_TYPE_WEIGHTS
from app.data import fundamentals_derived, fundamentals_fetch
from app.db.models import Stock
from app.db.session import SessionLocal
from app.ml import forecast_model

log = logging.getLogger("scheduler.jobs")

# Parameter default job (selaras default endpoint).
SCREENER_LIMIT = 10
RANKING_LIMIT = 80
REPORT_USE_ML = True


def _tradable_tickers(db) -> list[str]:
    """Daftar ticker saham (indeks dikecualikan) urut alfabetis."""
    tickers = db.scalars(select(Stock.ticker).order_by(Stock.ticker))
    return [t for t in tickers if not is_index(t)]


def job_update_market_data(tickers: list[str] | None = None) -> int:
    """07:00 — Tarik OHLCV terbaru + hitung indikator -> upsert market_data.

    Mengembalikan total bar tersimpan. Cache lama dibiarkan kedaluwarsa via TTL
    (wrapper Redis no-op tidak mendukung wildcard delete).
    """
    with SessionLocal() as db:
        results = md.ingest_universe(db, tickers=tickers)
    total = sum(results.values())
    succeeded = sum(1 for count in results.values() if count > 0)
    log.info("update_market_data: %s/%s ticker OK, %s bar total", succeeded, len(results), total)
    return total


def job_refresh_fundamental_derived() -> int:
    """07:15 (Phase 3) — Refresh metrik fundamental harga-sensitif harian
    (PE/PBV/MarketCap/DividendYield) -> fundamental_derived."""
    with SessionLocal() as db:
        results = fundamentals_derived.refresh_derived(db)
    ok = sum(1 for saved in results.values() if saved)
    log.info("refresh_fundamental_derived: %s/%s ticker ter-refresh", ok, len(results))
    return ok


def job_run_all_strategies(limit: int = SCREENER_LIMIT) -> int:
    """07:30 (Phase 3) — Jalankan SEMUA 9 strategi -> strategy_results.

    Sumber untuk Strategy Matrix (Day 8), Strength Score (Day 9), Explain/Why
    (Day 10). Mengembalikan jumlah baris hasil yang dipersist.
    """
    with SessionLocal() as db:
        result = strategy_screener.screen_all_strategies(db, limit=limit)
    log.info(
        "run_all_strategies: %s baris dipersist (universe %s)",
        result["persisted"],
        result["universe"],
    )
    return result["persisted"]


def job_generate_forecasts(tickers: list[str] | None = None) -> int:
    """16:15 (Phase 3) — Probability Forecast 1D/5D/20D tiap saham -> tabel forecast."""
    generated = 0
    with SessionLocal() as db:
        if tickers is None:
            tickers = _tradable_tickers(db)
        for ticker in tickers:
            if is_index(ticker):
                continue
            result = forecast_model.predict_ticker(db, ticker)
            if result is None:  # bar kurang
                continue
            on_date = forecast_api._latest_date(db, ticker)
            if on_date is not None:
                forecast_api._persist(db, ticker, on_date, result)
                generated += 1
    log.info("generate_forecasts: %s forecast dipersist", generated)
    return generated


def job_generate_strength(tickers: list[str] | None = None) -> int:
    """16:30 (Phase 3) — Strength Score lintas-strategi tiap saham -> strength_score.

    Membaca strategy_results (harus jalan SETELAH job_run_all_strategies 07:30).
    """
    generated = 0
    with SessionLocal() as db:
        if tickers is None:
            tickers = _tradable_tickers(db)
        for ticker in tickers:
            if is_index(ticker):
                continue
            _result, on_date = strength_api.compute_for_ticker(
                db, ticker, dict(DEFAULT_TYPE_WEIGHTS), DEFAULT_FULL_POINTS, persist=True
            )
            if on_date is not None:
                generated += 1
    log.info("generate_strength: %s strength score dipersist", generated)
    return generated


def job_update_fundamentals(tickers: list[str] | None = None) -> int:
    """Mingguan (Phase 3) — Tarik ulang data fundamental dari Yahoo -> fundamentals.

    Fundamental berubah per kuartal; cukup di-refresh mingguan / saat rilis laporan.
    """
    with SessionLocal() as db:
        results = fundamentals_fetch.ingest_fundamentals(db, tickers=tickers)
    ok = sum(1 for count in results.values() if count > 0)
    log.info("update_fundamentals: %s/%s ticker OK", ok, len(results))
    return ok


def job_run_screener(limit: int = SCREENER_LIMIT) -> int:
    """09:30 / 10:00 / 15:30 — Jalankan screener (BSJP+BPJS) -> screening_history.

    run_screener menghitung kedua strategi dan mem-persist semua kandidat yang
    lolos pada bar terbaru (upsert idempoten). Mengembalikan jumlah yang disimpan.
    """
    with SessionLocal() as db:
        result = run_screener(db, limit=limit, use_ml=True)
    log.info("run_screener: %s kandidat dipersist", result["persisted"])
    return result["persisted"]


def job_generate_ranking(limit: int = RANKING_LIMIT, use_ml: bool = True) -> int:
    """16:00 — Hitung Composite Score ranking lalu hangatkan cache Redis."""
    with SessionLocal() as db:
        result = run_ranking(db, limit=limit, use_ml=use_ml)
    cache_key = RANKING_CACHE_KEY.format(limit=limit, ml=use_ml)
    redis_client.cache_set_json(cache_key, result, ttl=redis_client.TTL_RANKING)
    log.info("generate_ranking: %s saham di-rank & di-cache", result["ranked"])
    return result["ranked"]


def job_generate_reports(use_ml: bool = REPORT_USE_ML) -> int:
    """17:00 — Generate AI Stock Report tiap saham lalu hangatkan cache Redis."""
    generated = 0
    with SessionLocal() as db:
        tickers = list(db.scalars(select(Stock.ticker).order_by(Stock.ticker)))
        for ticker in tickers:
            bars = stock_report._load_bars(db, ticker)
            if len(bars) < stock_report.MIN_BARS:
                continue
            payload = stock_report.assemble_report_payload(db, ticker, bars, use_ml)
            cache_key = stock_report.CACHE_KEY.format(ticker=ticker, ml=use_ml)
            redis_client.cache_set_json(cache_key, payload, ttl=redis_client.TTL_REPORT)
            generated += 1
    log.info("generate_reports: %s report dibuat & di-cache", generated)
    return generated
