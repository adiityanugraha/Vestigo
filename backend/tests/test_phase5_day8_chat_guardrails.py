"""Phase 5 Day 8 — Chat guardrails & konteks.

Out-of-scope (tanpa LLM), scope pre-filter, cache key, anti-injeksi, load_history,
multi-turn, dan cache jawaban identik. Tes berat-LLM di-gate (AI/DB).
"""

from __future__ import annotations

import uuid

import pytest

from app.ai import chat_engine, guardrails


# --------------------------------------------------------------------------- #
# Scope & guardrails (murni / tanpa LLM)
# --------------------------------------------------------------------------- #
def test_is_in_scope():
    known = {"BBCA", "BMRI"}
    assert guardrails.is_in_scope("Berapa harga saham BBCA?", known) is True
    assert guardrails.is_in_scope("Apa itu RSI?", known) is True            # keyword
    assert guardrails.is_in_scope("BBCA gimana?", known) is True            # ticker
    assert guardrails.is_in_scope("Resep nasi goreng enak", known) is False
    assert guardrails.is_in_scope("Cuaca besok bagaimana?", known) is False


def test_system_rules_has_antiinjection():
    assert "ANTI-INJEKSI" in guardrails.SYSTEM_RULES


def test_cache_key_normalization():
    assert chat_engine._cache_key("  Apa   itu RSI? ") == chat_engine._cache_key("apa itu rsi?")


def test_out_of_scope_answer_no_llm():
    # Pertanyaan jelas di luar topik -> redirect baku TANPA memanggil LLM.
    out = chat_engine.answer("Resep nasi goreng spesial untuk makan malam")
    assert out == guardrails.OUT_OF_SCOPE_MESSAGE
    assert "cakupan" in out.lower()
    assert "bukan nasihat keuangan" in out.lower()


# --------------------------------------------------------------------------- #
# load_history (DB; tanpa LLM)
# --------------------------------------------------------------------------- #
def test_load_history():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError
    from app.db.models import ChatHistory

    sid = f"test-{uuid.uuid4().hex}"
    try:
        with SessionLocal() as db:
            db.add(ChatHistory(session_id=sid, role="user", message="halo"))
            db.add(ChatHistory(session_id=sid, role="assistant", message="hai"))
            db.commit()
        hist = chat_engine.load_history(sid)
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert [h["role"] for h in hist] == ["user", "assistant"]
    assert hist[0]["message"] == "halo"


def test_endpoint_out_of_scope_no_llm():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    try:
        r = client.post("/api/chat", json={"message": "Cuaca besok bagaimana?"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200
    assert "cakupan" in r.json()["answer"].lower()


# --------------------------------------------------------------------------- #
# Live: cache jawaban identik & multi-turn (gated AI+DB)
# --------------------------------------------------------------------------- #
def _skip_unless_ready():
    from app.db.session import SessionLocal
    from app.ai import llm_client

    if SessionLocal is None or not llm_client.is_available():
        pytest.skip("DB/AI belum siap.")


def test_cache_identical_answer():
    _skip_unless_ready()
    from sqlalchemy.exc import OperationalError

    q = "Apa itu support dan resistance dalam analisis saham?"
    try:
        a1 = chat_engine.answer(q)
        cached = chat_engine.redis_client.cache_get_json(chat_engine._cache_key(q))
        a2 = chat_engine.answer(q)
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert a1 == a2  # jawaban identik (kedua dari cache)
    # Cache terisi (kecuali Redis nonaktif -> cached None, toleransi).
    if cached is not None:
        assert isinstance(cached, str) and cached == a1


def test_multiturn_persist():
    _skip_unless_ready()
    from sqlalchemy import select, func
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import SessionLocal
    from app.db.models import ChatHistory

    client = TestClient(app)
    try:
        r1 = client.post("/api/chat", json={"message": "Bagaimana kondisi teknikal BBCA?"})
        sid = r1.json()["session_id"]
        r2 = client.post("/api/chat", json={"message": "Apakah dia sudah overbought?", "session_id": sid})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r2.status_code == 200
    assert r2.json()["answer"].strip()
    with SessionLocal() as db:
        n = db.scalar(select(func.count()).select_from(ChatHistory).where(ChatHistory.session_id == sid))
    assert n >= 4  # 2 user + 2 assistant
