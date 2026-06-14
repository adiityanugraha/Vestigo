"""Phase 4 Day 12 — Portfolio Builder.

Uji fungsi murni weight-cap + smoke DB/endpoint untuk tiap profil risiko.
"""

from __future__ import annotations

import pytest

from app.quant import portfolio_builder as pb


def test_apply_weight_cap_redistributes():
    # cap 0.4 feasible (3*0.4=1.2>=1); 0.5 di-cap, kelebihan ke B & C.
    w = pb.apply_weight_cap({"A": 0.5, "B": 0.3, "C": 0.2}, cap=0.4)
    assert w["A"] == pytest.approx(0.4, abs=1e-6)
    assert sum(w.values()) == pytest.approx(1.0)
    assert all(v <= 0.4 + 1e-6 for v in w.values())
    assert w["B"] > 0.3 and w["C"] > 0.2  # menerima redistribusi


def test_apply_weight_cap_infeasible_falls_back_equal():
    # 2 posisi, cap 0.2 → tak mungkin total 1; cap efektif = 1/n = 0.5.
    w = pb.apply_weight_cap({"A": 0.7, "B": 0.3}, cap=0.2)
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["A"] == pytest.approx(0.5)
    assert w["B"] == pytest.approx(0.5)


def test_apply_weight_cap_already_within_cap():
    w = pb.apply_weight_cap({"A": 0.4, "B": 0.35, "C": 0.25}, cap=0.5)
    assert w["A"] == pytest.approx(0.4)
    assert sum(w.values()) == pytest.approx(1.0)


def test_apply_weight_cap_empty():
    assert pb.apply_weight_cap({}, cap=0.3) == {}


def test_risk_profiles_defined():
    assert set(pb.RISK_PROFILES) == {"CONSERVATIVE", "MODERATE", "AGGRESSIVE"}
    # Conservative tak boleh memasukkan saham High Risk.
    assert "HIGH" not in pb.RISK_PROFILES["CONSERVATIVE"]["allowed_levels"]
    # Aggressive cap bobot > conservative (boleh lebih terkonsentrasi).
    assert (
        pb.RISK_PROFILES["AGGRESSIVE"]["weight_cap"]
        > pb.RISK_PROFILES["CONSERVATIVE"]["weight_cap"]
    )


def test_build_portfolio_each_profile():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test DB.")

    db = SessionLocal()
    try:
        for profile in ("CONSERVATIVE", "MODERATE", "AGGRESSIVE"):
            r = pb.build_portfolio(
                db, risk_profile=profile, capital=100_000_000, universe="lq45"
            )
            assert r["risk_profile"] == profile
            assert r["n_positions"] > 0
            cfg = pb.RISK_PROFILES[profile]
            assert r["n_positions"] <= cfg["max_positions"]

            weights = [a["weight"] for a in r["allocations"]]
            assert sum(weights) == pytest.approx(1.0, abs=1e-3)
            # Tiap bobot dalam cap efektif (>= cap karena bisa naik ke 1/n).
            assert all(w <= max(cfg["weight_cap"], 1.0 / r["n_positions"]) + 1e-3 for w in weights)
            # Total alokasi rupiah ~ modal.
            assert sum(a["amount"] for a in r["allocations"]) == pytest.approx(1e8, rel=1e-3)
            # Conservative: tak ada saham High Risk.
            if profile == "CONSERVATIVE":
                assert all(a["risk_level"] != "HIGH" for a in r["allocations"])
    finally:
        db.close()


def test_portfolio_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/portfolio-builder",
        json={"risk": "MODERATE", "capital": 50_000_000, "universe": "lq45"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["risk_profile"] == "MODERATE"
    assert body["n_positions"] > 0
    assert body["allocations"][0]["amount"] > 0
    assert body["disclaimer"]
    assert body["saved_id"] is None  # save default false

    assert client.post("/api/portfolio-builder", json={"risk": "NGAWUR"}).status_code == 422
    assert (
        client.post("/api/portfolio-builder", json={"risk": "MODERATE", "universe": "x"}).status_code
        == 422
    )
