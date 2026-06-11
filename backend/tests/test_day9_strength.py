"""Day 9 — Screener Strength Score.

Logika murni (compute_strength) diuji dengan daftar strategi lolos sintetis;
endpoint diuji dengan TestClient memakai strategy_results sungguhan (auto-skip
bila tak ada DB).
"""

from __future__ import annotations

import pytest

from app.core.strength_engine import (
    DEFAULT_FULL_POINTS,
    compute_strength,
    type_weight,
)


def test_type_weight_defaults() -> None:
    assert type_weight("technical") == 1.0
    assert type_weight("fundamental") == 1.5
    assert type_weight("unknown") == 1.0  # fallback


def test_no_passes_zero_strength() -> None:
    result = compute_strength("T", [])
    assert result.strength == 0
    assert result.points == 0.0
    assert result.passed_strategies == []


def test_single_technical_pass() -> None:
    result = compute_strength("T", [("bsjp", "technical")])
    # points 1.0 / full 6.0 -> 17
    assert result.points == 1.0
    assert result.strength == round(100 * 1.0 / 6.0)


def test_fundamental_weighted_heavier() -> None:
    tech = compute_strength("T", [("breakout", "technical")])
    fund = compute_strength("T", [("timeless", "fundamental")])
    assert fund.strength > tech.strength  # 1.5 vs 1.0


def test_multiple_passes_accumulate() -> None:
    passed = [
        ("bpjs", "technical"),       # 1.0
        ("cash_rich", "fundamental"),  # 1.5
        ("turnaround", "fundamental"),  # 1.5
        ("timeless", "fundamental"),    # 1.5
    ]
    result = compute_strength("LSIP", passed)
    assert result.points == 5.5
    assert result.strength == round(100 * 5.5 / 6.0)  # 92
    assert len(result.breakdown) == 4
    assert result.passed_strategies == ["bpjs", "cash_rich", "turnaround", "timeless"]


def test_strength_capped_at_100() -> None:
    # Banyak fundamental -> points > full_points -> mentok 100.
    passed = [(f"s{i}", "fundamental") for i in range(6)]  # 9.0 points
    result = compute_strength("T", passed)
    assert result.points == 9.0
    assert result.strength == 100


def test_configurable_weights_and_full_points() -> None:
    passed = [("timeless", "fundamental")]
    # Naikkan bobot fundamental & turunkan full_points -> skor lebih tinggi.
    result = compute_strength(
        "T", passed, weights={"technical": 1.0, "fundamental": 3.0}, full_points=3.0
    )
    assert result.points == 3.0
    assert result.strength == 100


def test_invalid_full_points_raises() -> None:
    with pytest.raises(ValueError):
        compute_strength("T", [], full_points=0)


def test_default_full_points_constant() -> None:
    assert DEFAULT_FULL_POINTS == 6.0


# --------------------------------------------------------------------------- #
# Endpoint (butuh DB + strategy_results terisi)
# --------------------------------------------------------------------------- #
def _client_or_skip():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test endpoint.")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_api_strength_known_ticker() -> None:
    client = _client_or_skip()
    resp = client.get("/api/strength/BBCA", params={"refresh": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "BBCA"
    assert 0 <= data["strength"] <= 100
    # passed_strategies konsisten dengan breakdown.
    assert [c["strategy"] for c in data["breakdown"]] == data["passed_strategies"]
    # points = jumlah bobot breakdown.
    assert abs(data["points"] - sum(c["weight"] for c in data["breakdown"])) < 1e-9


def test_api_strength_unknown_ticker_404() -> None:
    client = _client_or_skip()
    assert client.get("/api/strength/ZZZZ").status_code == 404


def test_api_strength_weights_change_score() -> None:
    client = _client_or_skip()
    # Cari saham yang lolos minimal 1 strategi fundamental via matrix.
    matrix = client.get("/api/strategy-matrix", params={"refresh": True}).json()["matrix"]
    target = None
    for row in matrix:
        if any(row["results"].get(k) for k in ("high_growth", "cash_rich", "turnaround", "timeless")):
            target = row["ticker"]
            break
    if target is None:
        pytest.skip("Tidak ada saham lolos strategi fundamental.")

    low = client.get(f"/api/strength/{target}", params={"fundamental_weight": 1.0, "refresh": True}).json()
    high = client.get(f"/api/strength/{target}", params={"fundamental_weight": 3.0, "refresh": True}).json()
    assert high["strength"] >= low["strength"]
