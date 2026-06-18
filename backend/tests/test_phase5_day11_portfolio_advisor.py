"""Phase 5 Day 11 — Portfolio AI Advisor.

Validasi input (cepat) + satu profil live (alokasi dari Portfolio Builder Phase 4
+ penjelasan LLM + disclaimer). Build portfolio cukup berat -> satu profil live.
"""

from __future__ import annotations

import pytest

from app.quant import portfolio_builder as pb


def _client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def test_risk_profiles_exist():
    assert {"CONSERVATIVE", "MODERATE", "AGGRESSIVE"} <= set(pb.RISK_PROFILES)


def test_invalid_risk_422():
    assert _client().post("/api/portfolio-advisor", json={"risk": "FOO"}).status_code == 422


def test_invalid_universe_422():
    r = _client().post("/api/portfolio-advisor", json={"risk": "MODERATE", "universe": "xyz"})
    assert r.status_code == 422


def test_bad_capital_422():
    r = _client().post("/api/portfolio-advisor", json={"risk": "MODERATE", "capital": -100})
    assert r.status_code == 422


def test_endpoint_moderate_live():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError

    try:
        r = _client().post("/api/portfolio-advisor", json={"risk": "MODERATE", "universe": "lq45"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if r.status_code == 422:
        pytest.skip("Tidak ada kandidat lolos filter untuk profil ini.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["risk_profile"] == "MODERATE"
    assert body["n_positions"] >= 1
    assert body["allocations"]
    for a in body["allocations"]:
        assert "ticker" in a and "weight" in a
    # Bobot total ~1.0 (alokasi dari sistem).
    assert abs(sum(a["weight"] for a in body["allocations"]) - 1.0) < 0.02
    assert body["explanation"].strip()
    assert body["disclaimer"]
