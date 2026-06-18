"""Natural Language Screener API (Phase 5 Day 9).

POST /api/natural-query
  Body: {query}. LLM menerjemahkan query -> filter screener; engine Phase 3
  mengeksekusi (LLM tidak memilih saham) -> kandidat + ringkasan AI.

  503 bila lapisan AI nonaktif/sibuk; 422 bila query kosong atau tak dapat
  diinterpretasikan ke strategi yang dikenal.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import llm_client, natural_query
from app.db.session import get_db

router = APIRouter(prefix="/api/natural-query", tags=["natural-query"])


class NaturalQueryRequest(BaseModel):
    query: str


@router.post("")
def post_natural_query(req: NaturalQueryRequest, db: Session = Depends(get_db)) -> dict:
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(status_code=422, detail="query tidak boleh kosong.")
    if not llm_client.is_available():
        raise HTTPException(status_code=503, detail="Lapisan AI nonaktif (GEMINI_API_KEY belum diisi).")
    try:
        return natural_query.run(query, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except llm_client.LLMError as exc:
        raise HTTPException(status_code=503, detail=f"Lapisan AI sedang sibuk: {exc}") from exc
