"""Phase 5 Day 6 — Explainable AI 2.0 (breakdown Composite Score).

Tes murni breakdown kontribusi (kedua cabang ML) + konsistensi dengan engine
Composite Score Phase 2 (DB) + narasi live (gated AI) + endpoint.
"""

from __future__ import annotations

import pytest

from app.ai import explain_score as es
from app.ai import llm_client


# --------------------------------------------------------------------------- #
# build_breakdown (murni)
# --------------------------------------------------------------------------- #
def test_breakdown_with_ml():
    scores = {"technical": 80, "momentum": 60, "volume": 50, "volatility": 40, "ml": 30}
    bd = es.build_breakdown(scores)
    assert bd["ml_available"] is True
    assert len(bd["components"]) == 5
    # overall = 80*.30 + 60*.25 + 50*.20 + 40*.10 + 30*.15 = 57.5
    assert bd["recomputed_overall"] == pytest.approx(57.5, abs=0.01)
    # Σ kontribusi == recomputed_overall; effective_weight == weight (ML ada).
    assert sum(c["contribution"] for c in bd["components"]) == pytest.approx(57.5, abs=0.05)
    assert all(c["effective_weight"] == c["weight"] for c in bd["components"])


def test_breakdown_without_ml_renormalized():
    scores = {"technical": 80, "momentum": 60, "volume": 50, "volatility": 40, "ml": None}
    bd = es.build_breakdown(scores)
    assert bd["ml_available"] is False
    assert len(bd["components"]) == 4
    # overall = (24+15+10+4)/0.85 = 62.35...
    assert bd["recomputed_overall"] == pytest.approx(53 / 0.85, abs=0.05)
    # bobot direnormalisasi: effective > nominal.
    tech = next(c for c in bd["components"] if c["component"] == "technical")
    assert tech["effective_weight"] > tech["weight"]


def test_schema_required():
    assert set(es.ANALYSIS_SCHEMA["required"]) == {"summary", "bullish_factors", "risk_factors"}


# --------------------------------------------------------------------------- #
# Konsistensi dengan engine Phase 2 (DB; tanpa LLM)
# --------------------------------------------------------------------------- #
def test_breakdown_matches_engine_live_db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError
    from app.ai import tools

    try:
        comp = tools.run_tool("get_composite_score", {"ticker": "BBCA"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if "error" in comp:
        pytest.skip(f"BBCA tak ter-ranking: {comp['error']}")

    bd = es.build_breakdown(comp["breakdown"])
    # recomputed harus cocok dengan overall_score engine (toleransi pembulatan).
    assert bd["recomputed_overall"] == pytest.approx(comp["overall_score"], abs=1.0)


# --------------------------------------------------------------------------- #
# Narasi live + endpoint (gated)
# --------------------------------------------------------------------------- #
def test_explain_narration_live():
    from app.db.session import SessionLocal

    if SessionLocal is None or not llm_client.is_available():
        pytest.skip("DB/AI belum siap.")
    from sqlalchemy.exc import OperationalError

    try:
        res = es.explain("BBCA")
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if res.get("error") and res.get("overall_score") is None:
        pytest.skip("BBCA belum cukup data.")
    assert res["breakdown"]
    assert res["ai_generated"] is True
    assert res["summary"]
    assert res["disclaimer"]


def test_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    try:
        r = client.get("/api/explain-score/BBCA")
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ticker"] == "BBCA"
    assert body["breakdown"]
    assert body["disclaimer"]
    assert client.get("/api/explain-score/ZZZZ").status_code == 404
