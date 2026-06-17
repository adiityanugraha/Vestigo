"""Chat With Stock API (Phase 5 Day 7).

POST /api/chat
  Tanya-jawab bahasa alami berbasis data Pocket Screener (RAG + tool call =
  grounding). Body: {message, session_id?, stream?}. Menyimpan pesan user &
  assistant ke chat_history (untuk konteks multi-giliran Day 8).

  stream=false (default): kembalikan JSON {session_id, answer, disclaimer}.
  stream=true            : kembalikan teks streaming (text/plain), session_id
                           ada di header X-Session-Id.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai import chat_engine, guardrails
from app.db.models import ChatHistory
from app.db.session import SessionLocal

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    disclaimer: str


def _save(session_id: str, role: str, message: str) -> None:
    """Simpan satu pesan ke chat_history (aman-gagal bila DB tak ada)."""
    if SessionLocal is None:
        return
    with SessionLocal() as db:
        db.add(ChatHistory(session_id=session_id, role=role, message=message))
        db.commit()


@router.post("")
def post_chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="message tidak boleh kosong.")
    session_id = req.session_id or uuid.uuid4().hex

    # Muat riwayat sesi (giliran SEBELUMNYA) untuk konteks multi-giliran, lalu
    # simpan pesan user saat ini.
    history = chat_engine.load_history(session_id)
    _save(session_id, "user", message)

    if req.stream:
        def generate():
            chunks: list[str] = []
            for piece in chat_engine.stream_answer(message, history):
                chunks.append(piece)
                yield piece
            _save(session_id, "assistant", "".join(chunks))

        return StreamingResponse(
            generate(),
            media_type="text/plain; charset=utf-8",
            headers={"X-Session-Id": session_id},
        )

    answer = chat_engine.answer(message, history)
    _save(session_id, "assistant", answer)
    return ChatResponse(
        session_id=session_id, answer=answer, disclaimer=guardrails.DISCLAIMER
    ).model_dump()
