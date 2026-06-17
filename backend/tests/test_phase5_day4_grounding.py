"""Phase 5 Day 4 — fondasi grounding: retriever + tools + prompt_builder + guardrails.

Tes murni (tanpa jaringan) + eksekusi tool terhadap DB lokal (di-skip bila DB
tak terkonfigurasi/terjangkau) + retrieval live (di-skip bila AI nonaktif/KB
belum di-seed).
"""

from __future__ import annotations

import pytest

from app.ai import guardrails, prompt_builder, tools
from app.rag import retriever, vector_store


# --------------------------------------------------------------------------- #
# guardrails (murni)
# --------------------------------------------------------------------------- #
def test_ensure_disclaimer_adds_when_missing():
    out = guardrails.ensure_disclaimer("BBCA momentum kuat.")
    assert "bukan nasihat keuangan" in out.lower()
    assert out.startswith("BBCA momentum kuat.")


def test_ensure_disclaimer_no_duplicate():
    once = guardrails.ensure_disclaimer("Analisis. " + guardrails.DISCLAIMER)
    assert once.lower().count("bukan nasihat keuangan") == 1


def test_ensure_disclaimer_empty():
    assert guardrails.ensure_disclaimer("") == guardrails.DISCLAIMER


# --------------------------------------------------------------------------- #
# prompt_builder (murni)
# --------------------------------------------------------------------------- #
def test_build_prompt_layers():
    built = prompt_builder.build(
        "Kenapa BBCA menarik?",
        rag_context="- Composite Score: skor 0-100.",
        tool_results={"composite": {"overall_score": 88}},
    )
    assert "system" in built and "prompt" in built
    # Aturan guardrails ada di instruksi sistem.
    assert "GROUNDING" in built["system"]
    assert "Pocket Screener" in built["system"]
    # Prompt memuat konteks RAG, angka tool, dan pertanyaan.
    assert "Composite Score" in built["prompt"]
    assert "88" in built["prompt"]
    assert "Kenapa BBCA menarik?" in built["prompt"]


def test_build_prompt_minimal():
    built = prompt_builder.build("Halo")
    assert "Halo" in built["prompt"]
    assert built["system"]


# --------------------------------------------------------------------------- #
# tools registry (murni)
# --------------------------------------------------------------------------- #
def test_tool_specs_structure():
    specs = tools.tool_specs()
    assert len(specs) == len(tools.TOOLS)
    for s in specs:
        assert {"name", "description", "parameters"} <= s.keys()
        assert s["parameters"]["type"] == "object"
    names = {s["name"] for s in specs}
    assert {"get_market_data", "get_risk", "get_sector_rotation", "get_composite_score"} <= names


def test_run_tool_unknown():
    assert "error" in tools.run_tool("tidak_ada")


def test_run_tool_missing_ticker():
    out = tools.run_tool("get_market_data", {})
    assert "error" in out


# --------------------------------------------------------------------------- #
# Eksekusi tool terhadap DB (di-skip bila DB tak ada)
# --------------------------------------------------------------------------- #
def _skip_if_no_db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati eksekusi tool DB.")


def test_tool_market_data_live_db():
    _skip_if_no_db()
    from sqlalchemy.exc import OperationalError

    try:
        out = tools.run_tool("get_market_data", {"ticker": "BBCA"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if "error" in out:
        pytest.skip(f"market_data BBCA belum ada: {out['error']}")
    assert out["ticker"] == "BBCA"
    assert out["close"] is not None


def test_tool_sector_rotation_live_db():
    _skip_if_no_db()
    from sqlalchemy.exc import OperationalError

    try:
        out = tools.run_tool("get_sector_rotation")
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if "error" in out:
        pytest.skip(f"sektor belum cukup: {out['error']}")
    assert out["market_ticker"] == "IHSG"


def test_tool_composite_and_risk_live_db():
    _skip_if_no_db()
    from sqlalchemy.exc import OperationalError

    try:
        comp = tools.run_tool("get_composite_score", {"ticker": "BBCA"})
        risk = tools.run_tool("get_risk", {"ticker": "BBCA"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if "error" not in comp:
        assert 0 <= comp["overall_score"] <= 100
        assert "breakdown" in comp
    if "error" not in risk:
        assert isinstance(risk, dict)  # smoke: tool mengembalikan payload risiko


# --------------------------------------------------------------------------- #
# Retriever (murni + live)
# --------------------------------------------------------------------------- #
def test_format_context_empty():
    assert retriever.format_context([]) == ""


def test_format_context_with_hits():
    ctx = retriever.format_context([{"title": "Sharpe Ratio", "content": "return per risiko"}])
    assert "Sharpe Ratio" in ctx and "return per risiko" in ctx


def test_retrieve_empty_query():
    assert retriever.retrieve("") == []


def test_retrieve_recall_live():
    from app.rag import embeddings

    if not embeddings.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi — lewati retrieval live.")
    if len(vector_store.get_store()) == 0:
        pytest.skip("Knowledge base belum di-seed (python -m app.rag.knowledge_base).")
    hits = retriever.retrieve("apa itu sharpe ratio", top_k=3)
    assert hits, "retrieval seharusnya mengembalikan konsep"
    assert any(h["id"] == "quant_sharpe" for h in hits)
    assert retriever.retrieve_context("strategi breakout").strip() != ""
