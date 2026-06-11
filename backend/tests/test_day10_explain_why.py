"""Day 10 — Explainable AI (/api/explain) & Explain Why Selected (/api/why).

Engine murni (interpretasi sinyal teknikal, confidence, gabungan) diuji dengan
snapshot sintetis; endpoint diuji dengan TestClient (auto-skip bila tak ada DB).
Fokus: penjelasan AKURAT sesuai data, bukan template.
"""

from __future__ import annotations

import pytest

from app.core.explain_engine import (
    ExplainSnapshot,
    build_explanation,
    confidence_from_probability,
    technical_bullish,
    technical_risk,
)


# --------------------------------------------------------------------------- #
# Confidence
# --------------------------------------------------------------------------- #
def test_confidence_from_probability() -> None:
    assert confidence_from_probability(0.92) == 92
    assert confidence_from_probability(0.0) == 0
    assert confidence_from_probability(1.0) == 100
    assert confidence_from_probability(None) == 50  # netral bila model tak ada
    assert confidence_from_probability(1.5) == 100  # clamp


# --------------------------------------------------------------------------- #
# Sinyal bullish
# --------------------------------------------------------------------------- #
def test_bullish_macd_volume_rsi() -> None:
    s = ExplainSnapshot(
        close=1000, rsi=62, macd=5.0, macd_signal=3.0, macd_histogram=2.0,
        vwap_ratio=0.02, volume_spike_ratio=1.42,
    )
    factors = technical_bullish(s)
    assert any("MACD" in f for f in factors)
    assert any("42%" in f for f in factors)        # volume +42%
    assert any("RSI sehat (62)" in f for f in factors)
    assert any("VWAP" in f for f in factors)


def test_no_bullish_when_weak() -> None:
    s = ExplainSnapshot(close=1000, rsi=45, macd=1.0, macd_signal=2.0, volume_spike_ratio=0.8)
    assert technical_bullish(s) == []


# --------------------------------------------------------------------------- #
# Sinyal risiko
# --------------------------------------------------------------------------- #
def test_risk_overbought_near_resistance_high_atr() -> None:
    s = ExplainSnapshot(
        close=1000, rsi=78, bb_position=0.95, atr_pct=0.06,
        macd=1.0, macd_signal=2.0, vwap_ratio=-0.03,
    )
    factors = technical_risk(s)
    assert any("Overbought (RSI 78)" in f for f in factors)
    assert any("resistance" in f for f in factors)
    assert any("Volatilitas tinggi" in f for f in factors)
    assert any("MACD melemah" in f for f in factors)
    assert any("di bawah VWAP" in f for f in factors)


def test_risk_oversold_and_support() -> None:
    s = ExplainSnapshot(close=1000, rsi=25, bb_position=0.05)
    factors = technical_risk(s)
    assert any("Oversold (RSI 25)" in f for f in factors)
    assert any("support" in f for f in factors)


# --------------------------------------------------------------------------- #
# Gabungan
# --------------------------------------------------------------------------- #
def test_build_explanation_combines_rule_and_ml() -> None:
    s = ExplainSnapshot(close=1000, rsi=62, macd=5.0, macd_signal=3.0, macd_histogram=2.0)
    matched = ["Revenue +18% YoY", "MA20 > MA50 > MA100 > MA200"]
    exp = build_explanation(s, probability_up=0.74, matched_factors=matched)
    assert exp.confidence == 74
    # rule-based factors didahulukan
    assert exp.bullish_factors[:2] == matched
    # ML-layer ditambahkan setelahnya
    assert any("MACD" in f for f in exp.bullish_factors)


def test_build_explanation_dedupes() -> None:
    s = ExplainSnapshot(close=1000, rsi=62)
    matched = ["RSI sehat (62) — momentum kuat tanpa overbought"]
    exp = build_explanation(s, 0.6, matched)
    # tidak menduplikasi faktor yang sama dari rule & ML
    assert exp.bullish_factors.count(matched[0]) == 1


def test_build_explanation_no_snapshot() -> None:
    exp = build_explanation(None, probability_up=None, matched_factors=["X"])
    assert exp.confidence == 50
    assert exp.bullish_factors == ["X"]
    assert exp.risk_factors == []


# --------------------------------------------------------------------------- #
# Endpoint (butuh DB)
# --------------------------------------------------------------------------- #
def _client_or_skip():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test endpoint.")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def _passing_ticker(client) -> str | None:
    matrix = client.get("/api/strategy-matrix", params={"refresh": True}).json()["matrix"]
    return matrix[0]["ticker"] if matrix else None


def test_api_explain_structure() -> None:
    client = _client_or_skip()
    resp = client.get("/api/explain/BBCA", params={"refresh": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "BBCA"
    assert 0 <= data["confidence"] <= 100
    assert isinstance(data["bullish_factors"], list)
    assert isinstance(data["risk_factors"], list)


def test_api_explain_404() -> None:
    client = _client_or_skip()
    assert client.get("/api/explain/ZZZZ").status_code == 404


def test_api_why_reasons_match_passed_strategies() -> None:
    client = _client_or_skip()
    ticker = _passing_ticker(client)
    if ticker is None:
        pytest.skip("Tidak ada saham lolos strategi apa pun.")
    data = client.get(f"/api/why/{ticker}", params={"refresh": True}).json()
    # `matched` (nama) sejajar dengan matched_strategies.
    assert data["matched"] == [m["name"] for m in data["matched_strategies"]]
    # reasons gabungan = konkatenasi reasons tiap strategi (akurat, bukan template).
    flat = [r for m in data["matched_strategies"] for r in m["reasons"]]
    assert data["reasons"] == flat
    # saham yang muncul di matrix harus punya >= 1 strategi cocok.
    assert len(data["matched"]) >= 1


def test_api_why_no_match_empty() -> None:
    # Ticker yang ada tapi (kemungkinan) tak lolos apa pun -> matched kosong, 200.
    client = _client_or_skip()
    resp = client.get("/api/why/TLKM", params={"refresh": True})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["matched"], list)
    assert body["matched"] == [m["name"] for m in body["matched_strategies"]]
