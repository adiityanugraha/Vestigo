"""FastAPI entrypoint — Pocket Screener Phase 2 backend.

Jalankan (dari folder backend/, venv aktif):
    uvicorn app.main:app --reload --port 8000

Health check: http://localhost:8000/api/health
Docs (Swagger): http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    benchmark,
    equity_curve,
    explain,
    forecast,
    fundamentals,
    health,
    history,
    market_breadth,
    market_data,
    performance,
    ranking,
    replay,
    risk,
    screener,
    stock_report,
    strategies,
    strategy_matrix,
    strength,
    support_resistance,
    why,
)
from app.core.config import get_settings
from app.scheduler import scheduler as scheduler_module

settings = get_settings()
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop scheduler job harian bersama siklus hidup aplikasi (Day 13)."""
    if settings.scheduler_enabled:
        scheduler_module.start()
    else:
        log.info("Scheduler dimatikan (SCHEDULER_ENABLED=false).")
    try:
        yield
    finally:
        scheduler_module.shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend Pocket Screener Phase 2: screener, scoring, analytics & reporting.",
    lifespan=lifespan,
)

# CORS — frontend (Next.js) memanggil API ini dari origin yang berbeda.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(performance.router)
app.include_router(equity_curve.router)
app.include_router(benchmark.router)
app.include_router(replay.router)
app.include_router(strategies.router)
app.include_router(strategy_matrix.router)
app.include_router(strength.router)
app.include_router(explain.router)
app.include_router(why.router)
app.include_router(forecast.router)
app.include_router(fundamentals.router)
app.include_router(screener.router)
app.include_router(market_data.router)
app.include_router(ranking.router)
app.include_router(stock_report.router)
app.include_router(risk.router)
app.include_router(support_resistance.router)
app.include_router(market_breadth.router)
app.include_router(history.router)


@app.get("/")
async def root() -> dict:
    return {
        "message": f"{settings.app_name} is running.",
        "docs": "/docs",
        "health": "/api/health",
    }
