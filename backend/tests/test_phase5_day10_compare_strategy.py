"""Phase 5 Day 10 — AI Strategy Comparator.

Tes murni validasi (hanya 5 strategi teknikal; tolak fundamental) + endpoint
live (metrik dari sistem + narasi). Anti-halusinasi: strategi tanpa metrik
historis ditolak, bukan dikarang.
"""

from __future__ import annotations

import pytest

from app.ai import strategy_comparator as sc
from app.quant import performance_metrics as pm


# --------------------------------------------------------------------------- #
# Validasi (murni)
# --------------------------------------------------------------------------- #
def test_validate_accepts_two_technical():
    a, b = sc._validate("Breakout", "trend_following")
    assert a == "breakout" and b == "trend_following"
    assert a in pm.VALIDATED_STRATEGIES and b in pm.VALIDATED_STRATEGIES


def test_validate_rejects_fundamental():
    with pytest.raises(ValueError):
        sc._validate("high_growth", "breakout")  # fundamental tak tervalidasi


def test_validate_rejects_same_and_unknown():
    with pytest.raises(ValueError):
        sc._validate("breakout", "breakout")
    with pytest.raises(ValueError):
        sc._validate("breakout", "tidak_ada")


# --------------------------------------------------------------------------- #
# Endpoint (DB-gated; AI opsional -> narasi tetap ada via template)
# --------------------------------------------------------------------------- #
def _client_or_skip():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def test_endpoint_compare_two_technical():
    client = _client_or_skip()
    from sqlalchemy.exc import OperationalError

    try:
        r = client.get("/api/compare-strategy", params={"a": "breakout", "b": "trend_following"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["strategy_a"] == "breakout" and body["strategy_b"] == "trend_following"
    # Metrik dari sistem (Phase 4) ada.
    assert "cagr" in body["metrics_a"] and "max_drawdown" in body["metrics_a"]
    assert "cagr" in body["metrics_b"]
    assert body["comparison"].strip()
    assert body["disclaimer"]


def test_endpoint_rejects_fundamental_and_same():
    client = _client_or_skip()
    from sqlalchemy.exc import OperationalError

    try:
        # Fundamental -> 422 (tak ada metrik historis; tidak dikarang).
        assert client.get("/api/compare-strategy", params={"a": "timeless", "b": "breakout"}).status_code == 422
        # Sama -> 422.
        assert client.get("/api/compare-strategy", params={"a": "breakout", "b": "breakout"}).status_code == 422
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    # Param wajib hilang -> 422.
    assert client.get("/api/compare-strategy", params={"a": "breakout"}).status_code == 422
