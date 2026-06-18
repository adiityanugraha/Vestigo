"""Phase 5 Day 9 — Natural Language Screener.

Tes murni (clamp limit, filter risiko, katalog strategi) + live (parse query ->
strategi, endpoint) yang di-gate AI/DB. LLM HANYA membuat filter; eksekusi
deterministik oleh engine Phase 3.
"""

from __future__ import annotations

import pytest

from app.ai import natural_query as nq


# --------------------------------------------------------------------------- #
# Murni
# --------------------------------------------------------------------------- #
def test_clamp_limit():
    assert nq._clamp_limit(0) == 1
    assert nq._clamp_limit(99) == nq.MAX_LIMIT
    assert nq._clamp_limit(5) == 5
    assert nq._clamp_limit("abc") == nq.DEFAULT_LIMIT


def test_risk_allowed():
    assert nq._risk_allowed("LOW", "MEDIUM") is True
    assert nq._risk_allowed("MEDIUM", "MEDIUM") is True
    assert nq._risk_allowed("HIGH", "LOW") is False
    assert nq._risk_allowed(None, "LOW") is False


def test_strategy_catalog():
    catalog = nq.strategy_catalog()
    keys = {s["key"] for s in catalog}
    assert len(catalog) >= 9
    assert {"breakout", "high_growth", "timeless"} <= keys


# --------------------------------------------------------------------------- #
# Live (gated AI; parse_query tak butuh DB)
# --------------------------------------------------------------------------- #
def test_parse_query_breakout_live():
    from app.ai import llm_client

    if not llm_client.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi.")
    filt = nq.parse_query("cari saham breakout terbaik minggu ini")
    assert filt["strategy"] == "breakout"
    assert filt["limit"] >= 1


def test_endpoint_growth_low_risk_live():
    from app.db.session import SessionLocal
    from app.ai import llm_client

    if SessionLocal is None or not llm_client.is_available():
        pytest.skip("DB/AI belum siap.")
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    try:
        r = client.post("/api/natural-query", json={"query": "saham growth dengan risiko rendah"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200, r.text
    body = r.json()
    # LLM membuat filter; strategi harus key valid & risiko terdeteksi LOW.
    assert body["filter"]["strategy"] in {s["key"] for s in nq.strategy_catalog()}
    assert body["filter"]["max_risk"] == "LOW"
    assert isinstance(body["candidates"], list)
    assert body["summary"].strip()
    assert body["disclaimer"]
    # Kandidat yang lolos filter risiko harus berlabel risiko <= LOW.
    for c in body["candidates"]:
        assert c.get("risk") == "LOW"


def test_endpoint_empty_query_422():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    assert client.post("/api/natural-query", json={"query": "  "}).status_code == 422
