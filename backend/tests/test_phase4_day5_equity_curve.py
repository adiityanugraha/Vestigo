"""Phase 4 Day 5 — Equity Curve Engine.

Uji logika peak/drawdown & konsistensi dengan Performance Metrics + smoke
DB/endpoint.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.quant import equity_curve as ec
from app.quant import performance_metrics as pm


class _FakeDB:
    """Stub: kembalikan cohort_returns tetap, lewati query DB."""

    def __init__(self, dates, returns):
        self._dr = (dates, returns)


def test_build_curve_peak_and_drawdown(monkeypatch):
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=30 * i) for i in range(5)]
    returns = [0.10, 0.10, -0.50, 0.10, 0.05]
    monkeypatch.setattr(pm, "cohort_returns", lambda db, s, **k: (dates, returns))

    points = ec.build_curve(None, "bsjp")
    values = [round(p["portfolio_value"], 4) for p in points]
    assert values == [1.10, 1.21, 0.605, 0.6655, 0.6988]

    # peak naik monoton lalu menahan di 1.21 selama drawdown.
    peaks = [round(p["peak"], 4) for p in points]
    assert peaks == [1.10, 1.21, 1.21, 1.21, 1.21]

    # drawdown 0 di puncak, terdalam saat value 0.605 (=-50%).
    assert points[0]["drawdown"] == pytest.approx(0.0)
    assert points[2]["drawdown"] == pytest.approx(0.605 / 1.21 - 1)
    assert min(p["drawdown"] for p in points) == pytest.approx(-0.5)


def test_curve_summary_consistent_with_max_drawdown(monkeypatch):
    dates = [dt.date(2020, 1, 1) + dt.timedelta(days=30 * i) for i in range(4)]
    returns = [0.2, -0.3, 0.1, 0.05]
    monkeypatch.setattr(pm, "cohort_returns", lambda db, s, **k: (dates, returns))

    points = ec.build_curve(None, "trend_following")
    summary = ec.curve_summary(points)
    assert summary["final_value"] == pytest.approx(points[-1]["portfolio_value"])
    assert summary["total_return"] == pytest.approx(points[-1]["portfolio_value"] - 1.0)
    assert summary["max_drawdown"] == pytest.approx(pm.max_drawdown([p["portfolio_value"] for p in points]))


def test_empty_returns_empty_curve(monkeypatch):
    monkeypatch.setattr(pm, "cohort_returns", lambda db, s, **k: ([], []))
    assert ec.build_curve(None, "bsjp") == []
    assert ec.curve_summary([])["final_value"] == 1.0


def test_curve_final_value_matches_performance_total_return():
    """Equity akhir = produk (1+return) — harus konsisten dgn metrik (DB)."""
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    db = SessionLocal()
    try:
        points = ec.build_curve(db, "trend_following")
        assert len(points) > 30
        # final_value harus = exp(sum log(1+r)) dari seri yang sama dengan Day 4.
        _, returns = pm.cohort_returns(db, "trend_following")
        expected = 1.0
        for r in returns:
            expected *= 1 + r
        assert points[-1]["portfolio_value"] == pytest.approx(expected)
    finally:
        db.close()


def test_endpoint_smoke_and_scaling():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    r = client.get("/api/equity-curve/bpjs?initial_capital=100000000")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy"] == "bpjs"
    assert len(body["points"]) > 30
    # nilai diskalakan ke modal awal (orde ratusan juta, bukan ~1.0).
    assert body["points"][0]["value"] > 1_000_000
    assert -1.0 <= body["summary"]["max_drawdown"] <= 0.0
    assert body["disclaimer"]

    assert client.get("/api/equity-curve/timeless").status_code == 404
    assert client.get("/api/equity-curve/bpjs?hold=2").status_code == 422
