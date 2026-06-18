"""Phase 5 Day 13 — AI Daily Report.

Tes murni format (Markdown & PDF dari report sintetis) + endpoint live (json/
markdown/pdf). Angka dari sistem; LLM menarasikan overview.
"""

from __future__ import annotations

import pytest

from app.ai import daily_report as dr

_SYNTHETIC = {
    "date": "2026-06-15",
    "overview": "Pasar cenderung menguat dengan sektor perbankan memimpin.",
    "top_opportunities": [
        {"ticker": "BBCA", "name": "Bank Central Asia", "overall_score": 88.5},
        {"ticker": "BMRI", "name": "Bank Mandiri", "overall_score": 81.2},
    ],
    "strongest_sector": "Banking & Finance",
    "weakest_sector": "Energy",
    "leading_sectors": ["Banking & Finance"],
    "lagging_sectors": ["Energy"],
    "high_confidence": [{"ticker": "BMRI", "prob_5d": 0.71, "prob_20d": 0.63, "confidence": "HIGH"}],
    "risk_warnings": [{"ticker": "GOTO", "risk": "HIGH", "score": 82}],
    "disclaimer": "Disclaimer: ini bukan nasihat keuangan.",
}


# --------------------------------------------------------------------------- #
# Format (murni)
# --------------------------------------------------------------------------- #
def test_to_markdown():
    md = dr.to_markdown(_SYNTHETIC)
    assert "Laporan Harian Pocket Screener" in md
    assert "2026-06-15" in md
    assert "Top Opportunities" in md
    assert "BBCA" in md and "GOTO" in md
    assert "bukan nasihat keuangan" in md.lower()


def test_to_pdf_bytes():
    data = dr.to_pdf(_SYNTHETIC)
    assert isinstance(data, (bytes, bytearray))
    assert bytes(data[:4]) == b"%PDF"


def test_latin1_sanitize():
    out = dr._latin1("naik ≥ 5% dan turun — risiko")
    out.encode("latin-1")  # tidak boleh melempar
    assert "naik" in out and "risiko" in out


# --------------------------------------------------------------------------- #
# Endpoint live (DB-gated; satu build di-cache untuk semua format)
# --------------------------------------------------------------------------- #
def test_endpoint_all_formats_live():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    try:
        rj = client.get("/api/daily-report", params={"format": "json", "refresh": True})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if rj.status_code == 404:
        pytest.skip("Data laporan belum tersedia.")
    assert rj.status_code == 200, rj.text
    body = rj.json()
    assert "top_opportunities" in body
    assert body["overview"].strip()
    assert body["disclaimer"]

    # markdown & pdf memakai laporan yang sama (cache) -> ringan, tanpa LLM ulang.
    rm = client.get("/api/daily-report", params={"format": "markdown"})
    assert rm.status_code == 200
    assert "text/markdown" in rm.headers["content-type"]
    assert "Laporan Harian" in rm.text

    rp = client.get("/api/daily-report", params={"format": "pdf"})
    assert rp.status_code == 200
    assert rp.headers["content-type"] == "application/pdf"
    assert rp.content[:4] == b"%PDF"
