"""Phase 5 Day 2 — Sector Rotation.

Tes fungsi murni (window_return, classify_quadrant, compute_rotation) dengan data
sintetis + smoke DB/endpoint yang di-skip bila DB tak terjangkau (termasuk kuota
Neon free tier terlampaui).
"""

from __future__ import annotations

import pytest

from app.core import sector_rotation as sr


# --------------------------------------------------------------------------- #
# Fungsi murni
# --------------------------------------------------------------------------- #
def test_window_return_basic_and_insufficient():
    closes = [10.0, 11.0, 12.0, 13.0]
    assert sr.window_return(closes, 1) == pytest.approx(13 / 12 - 1)
    assert sr.window_return(closes, 3) == pytest.approx(13 / 10 - 1)
    assert sr.window_return(closes, 4) is None   # butuh window+1 titik
    assert sr.window_return([], 1) is None
    assert sr.window_return([0.0, 5.0], 1) is None  # base <= 0


def test_classify_quadrant():
    assert sr.classify_quadrant(0.1, 0.05) == "LEADING"
    assert sr.classify_quadrant(0.1, -0.05) == "WEAKENING"
    assert sr.classify_quadrant(-0.1, -0.05) == "LAGGING"
    assert sr.classify_quadrant(-0.1, 0.05) == "IMPROVING"
    assert sr.classify_quadrant(None, 0.1) == "UNKNOWN"
    assert sr.classify_quadrant(0.1, None) == "UNKNOWN"


def _geo_series(daily_growth: float, n: int = 130, start: float = 100.0) -> list[float]:
    """Seri close dengan pertumbuhan harian konstan (untuk RS yang dapat diprediksi)."""
    return [start * ((1 + daily_growth) ** i) for i in range(n)]


def test_compute_rotation_relative_strength_and_ranking():
    market = _geo_series(0.0010)              # IHSG +0.10%/hari
    sector_a = _geo_series(0.0030)            # outperform -> RS > 0
    sector_b = _geo_series(0.0005)            # underperform -> RS < 0

    result = sr.compute_rotation(
        [
            sr.SectorInput("A", [sector_a, sector_a]),  # 2 anggota identik
            sr.SectorInput("B", [sector_b]),
        ],
        market,
        as_of="2026-06-11",
    )

    assert result.market_available is True
    by_name = {s.sector: s for s in result.sectors}

    # Sektor A mengungguli pasar di semua window; B di bawah pasar.
    assert by_name["A"].relative_strength["3m"] > 0
    assert by_name["B"].relative_strength["3m"] < 0
    assert by_name["A"].members == 2

    # Ranking by RS(3M): A terkuat (rank 1), B (rank 2).
    assert by_name["A"].rank == 1
    assert by_name["B"].rank == 2
    assert result.leaders[0] == "A"
    assert result.laggards[0] == "B"

    # Kuadran konsisten dengan tanda RS.
    assert by_name["A"].quadrant in ("LEADING", "WEAKENING")
    assert by_name["B"].quadrant in ("IMPROVING", "LAGGING")
    assert result.limitations == []


def test_compute_rotation_without_market_marks_limitation():
    sector_a = _geo_series(0.0030)
    result = sr.compute_rotation(
        [sr.SectorInput("A", [sector_a])],
        market_closes=[],                      # IHSG tak tersedia
        as_of="2026-06-11",
    )
    assert result.market_available is False
    a = result.sectors[0]
    assert a.returns["3m"] is not None          # return absolut tetap dihitung
    assert a.relative_strength["3m"] is None     # RS tidak bisa dihitung
    assert a.quadrant == "UNKNOWN"
    assert a.rank is None
    assert result.leaders == [] and result.laggards == []
    assert result.limitations  # ada catatan limitasi


# --------------------------------------------------------------------------- #
# Smoke DB / endpoint (di-skip bila DB tak terjangkau / kuota habis)
# --------------------------------------------------------------------------- #
def test_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke DB.")

    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    try:
        r = client.get("/api/sector-rotation?top=3")
    except OperationalError:
        pytest.skip("DB tak terjangkau (mis. kuota Neon habis) — lewati smoke.")

    if r.status_code == 404:
        pytest.skip("market_data/sektor belum cukup untuk dihitung.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["market_ticker"] == "IHSG"
    assert "1m" in body["windows"] and "3m" in body["windows"]
    assert isinstance(body["sectors"], list)
    # Bila ada sektor ter-rank, leaders tidak kosong.
    if any(s["rank"] is not None for s in body["sectors"]):
        assert body["leaders"]

    assert client.get("/api/sector-rotation?as_of=bad-date").status_code == 400
    assert client.get("/api/sector-rotation?top=99").status_code == 422
