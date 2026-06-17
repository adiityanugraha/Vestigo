"""Phase 5 Day 3 — RAG: vector store lokal + embeddings + knowledge base.

Tes murni vector store & struktur dokumen (tanpa jaringan) + smoke LIVE embedding
yang di-skip bila GEMINI_API_KEY belum dikonfigurasi (memakai sedikit kuota).
"""

from __future__ import annotations

import pytest

from app.rag import embeddings, knowledge_base as kb
from app.rag.vector_store import LocalVectorStore


# --------------------------------------------------------------------------- #
# Vector store (murni, tanpa jaringan)
# --------------------------------------------------------------------------- #
def _store_with(docs, vecs, tmp_path):
    s = LocalVectorStore(
        meta_path=tmp_path / "kb.meta.json", vec_path=tmp_path / "kb.vectors.npy"
    )
    s.replace(docs, vecs)
    return s


def test_search_ranking(tmp_path):
    docs = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
    vecs = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    store = _store_with(docs, vecs, tmp_path)

    hits = store.search([0.1, 0.9, 0.0], top_k=2)
    assert hits[0]["id"] == "B"
    assert 0.9 < hits[0]["score"] <= 1.0
    assert len(hits) == 2


def test_search_empty_store(tmp_path):
    store = LocalVectorStore(
        meta_path=tmp_path / "x.json", vec_path=tmp_path / "x.npy"
    )
    assert store.search([1.0, 0.0], top_k=3) == []


def test_save_load_roundtrip(tmp_path):
    docs = [{"id": "A", "title": "alpha"}, {"id": "B", "title": "beta"}]
    vecs = [[1.0, 0.0], [0.0, 1.0]]
    _store_with(docs, vecs, tmp_path).save()

    reloaded = LocalVectorStore(
        meta_path=tmp_path / "kb.meta.json", vec_path=tmp_path / "kb.vectors.npy"
    )
    assert reloaded.load() is True
    assert len(reloaded) == 2
    assert reloaded.search([0.0, 1.0], top_k=1)[0]["id"] == "B"


def test_replace_length_mismatch_raises(tmp_path):
    store = LocalVectorStore(meta_path=tmp_path / "m.json", vec_path=tmp_path / "v.npy")
    with pytest.raises(ValueError):
        store.replace([{"id": "A"}], [[1.0], [2.0]])


# --------------------------------------------------------------------------- #
# Knowledge base (struktur dokumen — murni)
# --------------------------------------------------------------------------- #
def test_documents_valid():
    docs = kb.DOCUMENTS
    assert len(docs) >= 30
    ids = [d["id"] for d in docs]
    assert len(ids) == len(set(ids)), "id dokumen harus unik"
    valid_sources = {"indicator", "strategy", "quant", "concept"}
    for d in docs:
        assert {"id", "source", "title", "content"} <= d.keys()
        assert d["source"] in valid_sources
        assert d["content"].strip()
    # Pastikan 9 strategi & metrik kunci tercakup.
    assert sum(1 for d in docs if d["source"] == "strategy") == 9
    assert any(d["id"] == "quant_sharpe" for d in docs)
    assert any(d["id"] == "concept_sector_rotation" for d in docs)


# --------------------------------------------------------------------------- #
# Smoke LIVE (di-skip bila AI nonaktif)
# --------------------------------------------------------------------------- #
def test_embed_dim_live():
    if not embeddings.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi — lewati smoke LIVE.")
    q = embeddings.embed_query("apa itu sharpe ratio")
    assert len(q) == embeddings.EMBED_DIM
    docs = embeddings.embed_documents(["RSI momentum", "Sharpe = return per risiko"])
    assert len(docs) == 2 and all(len(d) == embeddings.EMBED_DIM for d in docs)


def test_seed_and_retrieve_live(tmp_path):
    """Embed 3 dokumen nyata ke store sementara lalu pastikan retrieval relevan."""
    if not embeddings.is_available():
        pytest.skip("GEMINI_API_KEY belum dikonfigurasi — lewati smoke LIVE.")
    subset = [d for d in kb.DOCUMENTS if d["id"] in ("quant_sharpe", "strat_breakout", "ind_rsi")]
    store = LocalVectorStore(
        meta_path=tmp_path / "kb.meta.json", vec_path=tmp_path / "kb.vectors.npy"
    )
    vecs = embeddings.embed_documents([f"{d['title']}. {d['content']}" for d in subset])
    store.replace(subset, vecs)

    hits = store.search(embeddings.embed_query("imbal hasil per unit risiko"), top_k=1)
    assert hits[0]["id"] == "quant_sharpe"
