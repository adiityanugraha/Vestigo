"""AI Daily Report API (Phase 5 Day 13).

GET /api/daily-report?format=json|markdown|pdf
  Laporan harian: Top Opportunities, Strongest/Weakest Sector, High Confidence
  Stocks, Risk Warning + overview LLM. Angka dari sistem. Laporan terstruktur
  di-cache (Redis); markdown & PDF diturunkan dari laporan yang sama.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.ai import daily_report
from app.cache import redis_client
from app.db.session import get_db

router = APIRouter(prefix="/api/daily-report", tags=["daily-report"])

CACHE_KEY = "daily-report:latest"


def _get_report(db: Session, refresh: bool) -> dict:
    if not refresh:
        cached = redis_client.cache_get_json(CACHE_KEY)
        if cached is not None:
            cached["cached"] = True
            return cached
    report = daily_report.build_report(db)
    report["cached"] = False
    redis_client.cache_set_json(CACHE_KEY, report, ttl=redis_client.TTL_REPORT)
    return report


@router.get("")
def get_daily_report(
    format: str = Query("json", pattern="^(json|markdown|pdf)$"),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
):
    report = _get_report(db, refresh)
    if not report.get("date") and not report.get("top_opportunities"):
        raise HTTPException(status_code=404, detail="Data untuk laporan belum tersedia.")

    if format == "markdown":
        return PlainTextResponse(daily_report.to_markdown(report), media_type="text/markdown; charset=utf-8")
    if format == "pdf":
        return Response(
            daily_report.to_pdf(report),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=daily-report-{report.get('date') or 'latest'}.pdf"},
        )
    return report
