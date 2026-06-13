"""Phase 4 Day 4 — Advanced Performance Metrics.

Uji metrik MURNI terhadap nilai yang diketahui + smoke DB/endpoint.
"""

from __future__ import annotations

import math

import pytest

from app.quant import performance_metrics as pm

PPY = pm.TRADING_DAYS / pm.DEFAULT_HOLD  # periode/tahun untuk hold kanonik


def test_to_equity_and_max_drawdown():
    eq = pm.to_equity([0.10, -0.50, 0.10])
    assert eq[0] == pytest.approx(1.10)
    assert eq[1] == pytest.approx(0.55)
    assert eq[2] == pytest.approx(0.605)
    # puncak 1.10 → lembah 0.55 = -50%.
    assert pm.max_drawdown(eq) == pytest.approx(-0.5)


def test_max_drawdown_monotonic_up_is_zero():
    assert pm.max_drawdown(pm.to_equity([0.01, 0.02, 0.03])) == pytest.approx(0.0)


def test_cagr_doubling_over_two_years():
    # equity_end 2.0 dalam 2 tahun → ~41.42%.
    assert pm.cagr(2.0, 2.0) == pytest.approx(math.sqrt(2) - 1)


def test_sharpe_zero_volatility_is_zero():
    assert pm.sharpe([0.01, 0.01, 0.01], rf_period=0.0, periods_per_year=PPY) == 0.0


def test_sharpe_positive_when_mean_positive():
    returns = [0.01, -0.005, 0.012, 0.003, -0.002, 0.008]
    assert pm.sharpe(returns, rf_period=0.0, periods_per_year=PPY) > 0


def test_sortino_ignores_upside_volatility():
    a = [0.01, -0.01, 0.01, -0.01]
    b = [0.20, -0.01, 0.01, -0.01]  # lonjakan atas besar, downside sama
    assert pm.sortino(b, 0.0, PPY) >= pm.sortino(a, 0.0, PPY)


def test_profit_factor():
    # profit 0.3, loss 0.1 → PF 3.0.
    assert pm.profit_factor([0.1, 0.2, -0.1]) == pytest.approx(3.0)


def test_winrate_counts_only_active_periods():
    # 2 positif, 1 negatif, 2 kas(0) → winrate 2/3.
    assert pm.winrate([0.01, 0.0, -0.01, 0.02, 0.0]) == pytest.approx(2 / 3)


def test_calmar_and_recovery():
    assert pm.calmar(0.20, -0.10) == pytest.approx(2.0)
    assert pm.recovery_factor(0.40, -0.10) == pytest.approx(4.0)


def test_compute_metrics_empty_returns_zeros():
    m = pm.compute_metrics([], PPY)
    assert all(v == 0.0 for v in m.values())


def test_compute_metrics_keys_complete():
    returns = [0.05, -0.02, 0.03, 0.0, 0.01, -0.015, 0.04, 0.0, 0.02, -0.01]
    m = pm.compute_metrics(returns, PPY)
    for key in (
        "cagr", "winrate", "sharpe_ratio", "sortino_ratio", "calmar_ratio",
        "max_drawdown", "profit_factor", "recovery_factor",
    ):
        assert key in m


def test_compute_metrics_positive_series_positive_cagr():
    # Seri sebagian besar positif → CAGR & Sharpe positif, PF > 1.
    returns = [0.03, 0.02, -0.01, 0.04, 0.01, 0.02, -0.005, 0.03]
    m = pm.compute_metrics(returns, PPY)
    assert m["cagr"] > 0
    assert m["sharpe_ratio"] > 0
    assert m["profit_factor"] > 1


def test_compute_and_endpoint_smoke():
    """Hitung metrik nyata + cek endpoint bila DB tersedia."""
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    db = SessionLocal()
    try:
        result = pm.compute_for_strategy(db, "trend_following")
        assert result["n_periods"] > 30
        m = result["metrics"]
        assert -1.0 < m["max_drawdown"] <= 0.0
        assert m["profit_factor"] >= 0.0
    finally:
        db.close()

    client = TestClient(app)
    r = client.get("/api/performance/trend_following")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy"] == "trend_following"
    assert "sharpe_ratio" in body["metrics"]
    assert body["n_trades"] > 0
    assert body["hold"] == pm.DEFAULT_HOLD
    assert body["disclaimer"]

    # Strategi fundamental → 404 (tidak divalidasi historis).
    assert client.get("/api/performance/timeless").status_code == 404
    # Strategi tak dikenal → 404.
    assert client.get("/api/performance/ngawur").status_code == 404
    # Horizon tak valid → 422.
    assert client.get("/api/performance/trend_following?hold=2").status_code == 422
