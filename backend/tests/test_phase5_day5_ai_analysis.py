"""Phase 5 Day 5 — AI Analyst Engine.

Tes murni (confidence grounding logic, schema, tool baru) + smoke LIVE yang
membuktikan narasi memakai ANGKA SISTEM (confidence == Composite Score),
di-skip bila AI nonaktif / DB tak terjangkau.
"""

from __future__ import annotations

import pytest

from app.ai import ai_analysis, llm_client, tools


# --------------------------------------------------------------------------- #
# Murni
# --------------------------------------------------------------------------- #
def test_confidence_from_composite():
    assert ai_analysis._confidence({"get_composite_score": {"overall_score": 75.5}}) == 75.5
    assert ai_analysis._confidence({"get_composite_score": {"error": "x"}}) is None
    assert ai_analysis._confidence({}) is None


def test_analysis_schema():
    req = set(ai_analysis.ANALYSIS_SCHEMA["required"])
    assert req == {"summary", "bullish_factors", "risk_factors"}


def test_forecast_tool_registered():
    assert "get_forecast" in tools.TOOLS
    assert any(s["name"] == "get_forecast" for s in tools.tool_specs())


def test_is_retryable_classification():
    # Error transien (rate limit / overload) -> retry; error lain -> tidak.
    assert llm_client._is_retryable(Exception("429 RESOURCE_EXHAUSTED"))
    assert llm_client._is_retryable(Exception("503 UNAVAILABLE: overloaded"))
    assert not llm_client._is_retryable(Exception("Output LLM bukan JSON valid"))


# --------------------------------------------------------------------------- #
# Live grounding (di-skip bila AI nonaktif / DB tak ada)
# --------------------------------------------------------------------------- #
def _skip_unless_ready():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    if not llm_client.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi.")


def test_analyze_grounding_live():
    _skip_unless_ready()
    from sqlalchemy.exc import OperationalError

    try:
        res = ai_analysis.analyze("BBCA")
        comp = tools.run_tool("get_composite_score", {"ticker": "BBCA"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if res.get("error") and not res.get("date"):
        pytest.skip(f"data BBCA belum cukup: {res['error']}")

    assert res["ai_generated"] is True
    assert res["summary"]
    assert isinstance(res["bullish_factors"], list) and res["bullish_factors"]
    assert isinstance(res["risk_factors"], list)
    assert res["disclaimer"]
    # GROUNDING: confidence harus = Composite Score sistem (bukan karangan LLM).
    assert "error" not in comp
    assert res["confidence"] == comp["overall_score"]


def test_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    try:
        r = client.get("/api/ai-analysis/BBCA")
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ticker"] == "BBCA"
    assert body["disclaimer"]  # disclaimer WAJIB ada
    # ticker tak dikenal -> 404
    assert client.get("/api/ai-analysis/ZZZZ").status_code == 404
