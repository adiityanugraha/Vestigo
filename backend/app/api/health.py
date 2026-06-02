"""Health check endpoint (Day 1).

Mulai Day 2 & 4, endpoint ini akan diperluas untuk mengecek konektivitas
PostgreSQL & Redis. Untuk sekarang hanya melaporkan status aplikasi.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
