"""Chat With Stock — engine (Phase 5 Day 7).

Pipeline: query pengguna -> deteksi ticker -> kumpulkan ANGKA LIVE via tool
(grounding) + konteks konsep via RAG -> LLM merangkai jawaban + disclaimer.
Mendukung jawaban biasa (answer) & streaming (stream_answer).

Grounding: semua angka dari tool (Composite/Forecast/Risk/S-R/Sector/Breadth);
LLM tidak mengarang. Pemilihan tool berbasis ticker yang disebut + kata kunci
pasar (hemat: tool berat seperti market_breadth hanya dipanggil bila relevan).

Konteks multi-giliran (history) diterima sebagai parameter; pemanfaatan penuh
dari tabel chat_history dilakukan di Day 8.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from sqlalchemy import select

from app.ai import guardrails, llm_client, prompt_builder, tools
from app.db.models import Stock
from app.db.session import SessionLocal

_TICKER_TOOLS = (
    "get_composite_score",
    "get_market_data",
    "get_risk",
    "get_forecast",
    "get_support_resistance",
)
_SECTOR_KW = ("sektor", "sector", "rotasi", "rotation", "pasar", "market", "ihsg")
_BREADTH_KW = ("breadth", "gainer", "loser", "advancer", "decliner", "berapa saham", "naik turun")
_MAX_TICKERS = 2
_DISCLAIMER_MARK = "bukan nasihat keuangan"

_known_tickers: set[str] | None = None


def known_tickers() -> set[str]:
    """Set ticker IDX (cache di proses). Kosong bila DB tak terkonfigurasi."""
    global _known_tickers
    if _known_tickers is None:
        if SessionLocal is None:
            return set()
        with SessionLocal() as db:
            _known_tickers = {t for (t,) in db.execute(select(Stock.ticker)).all()}
    return _known_tickers


def detect_tickers(message: str, known: set[str] | None = None) -> list[str]:
    """Ekstrak ticker yang dikenal dari pesan (token 3-5 huruf, dicocokkan ke universe)."""
    known = known if known is not None else known_tickers()
    seen: set[str] = set()
    out: list[str] = []
    for token in re.findall(r"[A-Za-z]{3,5}", message):
        upper = token.upper()
        if upper in known and upper not in seen:
            seen.add(upper)
            out.append(upper)
    return out


def gather_context(message: str) -> dict[str, Any]:
    """Kumpulkan angka live relevan: tool per-ticker + konteks pasar bila relevan."""
    tickers = detect_tickers(message)[:_MAX_TICKERS]
    low = message.lower()
    data: dict[str, Any] = {}
    for ticker in tickers:
        data[ticker] = {
            name.replace("get_", ""): tools.run_tool(name, {"ticker": ticker})
            for name in _TICKER_TOOLS
        }
    if (not tickers) or any(kw in low for kw in _SECTOR_KW):
        data["sector_rotation"] = tools.run_tool("get_sector_rotation")
    if any(kw in low for kw in _BREADTH_KW):  # market_breadth berat -> hanya bila diminta
        data["market_breadth"] = tools.run_tool("get_market_breadth")
    return data


def _build(message: str, history: list[dict[str, str]] | None) -> dict[str, str]:
    from app.rag import retriever

    rag_context = retriever.retrieve_context(message, top_k=4)
    user_query = message
    if history:
        convo = "\n".join(f"{h['role']}: {h['message']}" for h in history[-6:])
        user_query = f"Riwayat percakapan sebelumnya:\n{convo}\n\nPertanyaan terbaru: {message}"
    return prompt_builder.build(user_query, rag_context=rag_context, tool_results=gather_context(message))


_AI_OFF = "Maaf, fitur AI sedang nonaktif (GEMINI_API_KEY belum diatur)."


def answer(message: str, history: list[dict[str, str]] | None = None, *, max_output_tokens: int = 800) -> str:
    """Jawaban chat (non-stream) ter-grounding + disclaimer."""
    if not llm_client.is_available():
        return f"{_AI_OFF}\n\n{guardrails.DISCLAIMER}"
    built = _build(message, history)
    try:
        text = llm_client.generate(
            built["prompt"], system=built["system"], max_output_tokens=max_output_tokens
        )
    except llm_client.LLMError:
        # Degradasi anggun: jangan biarkan error transien menjatuhkan endpoint.
        text = (
            "Maaf, layanan AI sedang sibuk dan tidak dapat menjawab saat ini. "
            "Silakan coba lagi sebentar lagi."
        )
    return guardrails.ensure_disclaimer(text)


def stream_answer(
    message: str, history: list[dict[str, str]] | None = None, *, max_output_tokens: int = 800
) -> Iterator[str]:
    """Jawaban chat streaming (yield potongan teks); disclaimer disisipkan di akhir."""
    if not llm_client.is_available():
        yield f"{_AI_OFF}\n\n{guardrails.DISCLAIMER}"
        return
    built = _build(message, history)
    produced: list[str] = []
    try:
        for chunk in llm_client.stream(
            built["prompt"], system=built["system"], max_output_tokens=max_output_tokens
        ):
            produced.append(chunk)
            yield chunk
    except llm_client.LLMError:
        # Degradasi anggun bila stream gagal sebelum/selagi mengalir.
        if not produced:
            yield "Maaf, layanan AI sedang sibuk. Silakan coba lagi sebentar lagi."
    if _DISCLAIMER_MARK not in "".join(produced).lower():
        yield f"\n\n{guardrails.DISCLAIMER}"
