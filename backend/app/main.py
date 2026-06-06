"""FastAPI entrypoint — Pocket Screener Phase 2 backend.

Jalankan (dari folder backend/, venv aktif):
    uvicorn app.main:app --reload --port 8000

Health check: http://localhost:8000/api/health
Docs (Swagger): http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, market_data, ranking, risk, screener, stock_report
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend Pocket Screener Phase 2: screener, scoring, analytics & reporting.",
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
app.include_router(screener.router)
app.include_router(market_data.router)
app.include_router(ranking.router)
app.include_router(stock_report.router)
app.include_router(risk.router)


@app.get("/")
async def root() -> dict:
    return {
        "message": f"{settings.app_name} is running.",
        "docs": "/docs",
        "health": "/api/health",
    }
