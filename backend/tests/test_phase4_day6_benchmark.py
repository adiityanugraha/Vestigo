"""Phase 4 Day 6 — Strategy Benchmark Engine.

Uji perakitan tabel benchmark + baris pasar IHSG + flag mengalahkan pasar.
Sebagian besar butuh DB (auto-skip bila tak ada).
"""

from __future__ import annotations

import pytest

from app.quant import benchmark as bench
from app.quant import performance_metrics as pm


def _db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test DB.")
    return SessionLocal()


def test_index_cohort_returns_shape():
    db = _db()
    try:
        dates, returns = bench.index_cohort_returns(db, hold=30)
        assert len(dates) == len(returns)
        assert len(returns) > 30  # ~10 thn / 30 hari bursa
        # return blok wajar (indeks tak bergerak ratusan persen per 30 hari).
        assert all(-0.6 < r < 0.6 for r in returns)
    finally:
        db.close()


def test_compute_benchmark_structure_and_flags():
    db = _db()
    try:
        result = bench.compute_benchmark(db, persist=True)
        assert result["market"]["is_benchmark"] is True
        assert result["market"]["strategy"] == "ihsg"
        assert len(result["strategies"]) == len(pm.VALIDATED_STRATEGIES)

        # Diurutkan CAGR menurun.
        cagrs = [r["metrics"]["cagr"] for r in result["strategies"]]
        assert cagrs == sorted(cagrs, reverse=True)

        # Flag konsisten dengan perbandingan CAGR ke pasar.
        market_cagr = result["market"]["metrics"]["cagr"]
        for r in result["strategies"]:
            assert r["beats_market_cagr"] == (r["metrics"]["cagr"] > market_cagr)
            assert "sharpe_ratio" in r["metrics"]
    finally:
        db.close()


def test_benchmark_persists_ihsg_row():
    db = _db()
    try:
        bench.compute_benchmark(db, persist=True)
        from sqlalchemy import select

        from app.db.models import StrategyPerformance

        row = db.scalar(
            select(StrategyPerformance).where(StrategyPerformance.strategy == "ihsg")
        )
        assert row is not None
        assert row.cagr is not None
    finally:
        db.close()


def test_benchmark_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    r = client.get("/api/benchmark")
    assert r.status_code == 200
    body = r.json()
    assert body["market"]["strategy"] == "ihsg"
    assert len(body["strategies"]) == 5
    assert body["disclaimer"]

    assert client.get("/api/benchmark?hold=2").status_code == 422
