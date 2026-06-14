"""Phase 4 Day 10 — Monte Carlo Simulation.

Uji bootstrap & ringkasan (deterministik via seed) + smoke DB/endpoint.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.quant import monte_carlo as mc


def test_simulate_shape_and_reproducibility():
    returns = [0.05, -0.02, 0.03, 0.01, -0.04, 0.06]
    a = mc.simulate(returns, n_periods=8, n_sims=2000, seed=42)
    b = mc.simulate(returns, n_periods=8, n_sims=2000, seed=42)
    assert a.shape == (2000,)
    assert np.array_equal(a, b)  # seed tetap → reproducible


def test_simulate_empty_inputs():
    assert mc.simulate([], 8).size == 0
    assert mc.simulate([0.1], 0).size == 0


def test_all_positive_returns_profit_certain():
    paths = mc.simulate([0.01, 0.02, 0.03], n_periods=8, n_sims=3000)
    s = mc.summarize(paths)
    assert s["probability_of_profit"] == pytest.approx(1.0)
    assert s["percentiles"]["p5"] > 0


def test_all_negative_returns_profit_zero():
    paths = mc.simulate([-0.01, -0.02, -0.03], n_periods=8, n_sims=3000)
    s = mc.summarize(paths)
    assert s["probability_of_profit"] == pytest.approx(0.0)
    assert s["percentiles"]["p95"] < 0


def test_percentiles_ordered_and_histogram():
    returns = [0.05, -0.03, 0.02, 0.04, -0.06, 0.01, 0.03, -0.02]
    s = mc.summarize(mc.simulate(returns, n_periods=8, n_sims=5000))
    p = s["percentiles"]
    assert p["p5"] <= p["p25"] <= p["p50"] <= p["p75"] <= p["p95"]
    assert 0.0 <= s["probability_of_profit"] <= 1.0
    assert len(s["histogram"]) == mc.HISTOGRAM_BINS
    assert sum(b["count"] for b in s["histogram"]) == 5000


def test_summarize_empty():
    s = mc.summarize(np.empty(0))
    assert s["probability_of_profit"] == 0.0
    assert s["histogram"] == []


def test_strategy_and_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    db = SessionLocal()
    try:
        r = mc.monte_carlo_strategy(db, "bpjs", n_sims=3000)
        assert r["simulations"] == 3000
        assert r["n_periods"] >= 1
        p = r["percentiles"]
        assert p["p5"] <= p["p50"] <= p["p95"]
        assert 0.0 <= r["probability_of_profit"] <= 1.0
    finally:
        db.close()

    client = TestClient(app)
    resp = client.get("/api/monte-carlo/bpjs?simulations=3000")
    assert resp.status_code == 200
    body = resp.json()
    assert body["strategy"] == "bpjs"
    assert body["simulations"] == 3000
    assert "p50" in body["percentiles"]
    assert body["disclaimer"]

    assert client.get("/api/monte-carlo/timeless").status_code == 404
    assert client.get("/api/monte-carlo/bpjs?simulations=10").status_code == 422  # < 1000
