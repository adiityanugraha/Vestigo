"""Phase 4 Day 8 — Risk Exposure per strategi.

Uji fungsi murni (losing streak, beta, klasifikasi) + smoke DB/endpoint.
"""

from __future__ import annotations

import pytest

from app.quant import risk_profile as rp


def test_longest_losing_streak():
    assert rp.longest_losing_streak([]) == 0
    assert rp.longest_losing_streak([0.1, 0.2, 0.3]) == 0
    assert rp.longest_losing_streak([-0.1, -0.2, 0.1, -0.3]) == 2
    assert rp.longest_losing_streak([-0.1, -0.2, -0.3]) == 3
    # kas (0) tidak menambah & tidak mereset.
    assert rp.longest_losing_streak([-0.1, 0.0, -0.2, 0.1, -0.1]) == 2


def test_beta_perfect_correlation_is_one():
    m = [0.01, -0.02, 0.03, -0.01, 0.02]
    assert rp.beta(m, m) == pytest.approx(1.0)


def test_beta_double_amplitude_is_two():
    m = [0.01, -0.02, 0.03, -0.01, 0.02]
    s = [2 * x for x in m]
    assert rp.beta(s, m) == pytest.approx(2.0)


def test_beta_zero_for_insufficient_or_flat_market():
    assert rp.beta([0.1], [0.1]) == 0.0
    assert rp.beta([0.1, 0.2], [0.05, 0.05]) == 0.0  # var pasar nol


def test_classify_thresholds():
    assert rp.classify(0.45, -0.30) == "HIGH"   # vol tinggi
    assert rp.classify(0.20, -0.70) == "HIGH"   # dd dalam
    assert rp.classify(0.20, -0.30) == "LOW"    # keduanya rendah
    assert rp.classify(0.30, -0.45) == "MEDIUM"  # di antara


def test_compute_and_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    db = SessionLocal()
    try:
        p = rp.compute_risk_profile(db, "trend_following")
        assert p["volatility"] > 0
        assert -1.0 < p["max_drawdown"] <= 0.0
        assert p["losing_streak"] >= 0
        assert p["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert p["avg_atr_pct"] is None or p["avg_atr_pct"] > 0
        # Strategi teknikal long-only → beta vs IHSG umumnya positif.
        assert p["beta"] > 0
    finally:
        db.close()

    client = TestClient(app)
    r = client.get("/api/risk-profile/bpjs")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy"] == "bpjs"
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert "vol_high" in body["thresholds"]
    assert body["disclaimer"]

    assert client.get("/api/risk-profile/timeless").status_code == 404
    assert client.get("/api/risk-profile/bpjs?hold=2").status_code == 422
