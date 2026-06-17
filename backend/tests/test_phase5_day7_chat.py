"""Phase 5 Day 7 — Chat With Stock (engine + endpoint).

Tes murni deteksi ticker + smoke endpoint (non-stream & stream) yang menyimpan
chat_history. LLM call di-skip-kan secara implisit aman: bila AI nonaktif,
endpoint tetap 200 dengan pesan + disclaimer.
"""

from __future__ import annotations

import pytest

from app.ai import chat_engine


# --------------------------------------------------------------------------- #
# Deteksi ticker (murni)
# --------------------------------------------------------------------------- #
def test_detect_tickers():
    known = {"BBCA", "BMRI", "TLKM"}
    assert chat_engine.detect_tickers("Mengapa BBCA mendapat skor tinggi?", known) == ["BBCA"]
    assert chat_engine.detect_tickers("bandingkan BBCA dan BMRI", known) == ["BBCA", "BMRI"]
    assert chat_engine.detect_tickers("halo dunia", known) == []
    # token bukan ticker (mis. 'RSI') tidak terdeteksi.
    assert chat_engine.detect_tickers("apa itu rsi", known) == []
    # tidak duplikat.
    assert chat_engine.detect_tickers("BBCA BBCA BBCA", known) == ["BBCA"]


def test_chat_history_model_importable():
    from app.db.models import ChatHistory

    assert ChatHistory.__tablename__ == "chat_history"


# --------------------------------------------------------------------------- #
# Endpoint (DB-gated; AI-agnostic untuk struktur)
# --------------------------------------------------------------------------- #
def _client_or_skip():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_chat_empty_message_422():
    client = _client_or_skip()
    assert client.post("/api/chat", json={"message": "   "}).status_code == 422


def test_chat_nonstream_and_persist():
    client = _client_or_skip()
    from sqlalchemy import select, func
    from sqlalchemy.exc import OperationalError
    from app.db.session import SessionLocal
    from app.db.models import ChatHistory

    try:
        r = client.post("/api/chat", json={"message": "Mengapa BBCA mendapat skor composite tinggi?"})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"].strip()
    assert body["disclaimer"]
    sid = body["session_id"]
    assert sid

    # user + assistant tersimpan ke chat_history.
    with SessionLocal() as db:
        n = db.scalar(select(func.count()).select_from(ChatHistory).where(ChatHistory.session_id == sid))
    assert n >= 2


def test_chat_stream():
    client = _client_or_skip()
    from sqlalchemy.exc import OperationalError

    try:
        r = client.post("/api/chat", json={"message": "Apa itu RSI?", "stream": True})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r.status_code == 200, r.text
    assert r.headers.get("x-session-id")
    assert r.text.strip()  # ada konten ter-stream
