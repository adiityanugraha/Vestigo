"""Phase 5 Day 12 — Market Narrator.

Tes murni ekstraksi field kunci + endpoint live (narasi pasar + persist
market_narratives). Angka dari sistem; LLM menarasikan.
"""

from __future__ import annotations

import pytest

from app.ai import market_narrator as mn


# --------------------------------------------------------------------------- #
# _extract (murni)
# --------------------------------------------------------------------------- #
def test_extract_key_fields():
    data = {
        "market_breadth": {"date": "2026-06-15", "bullish_ratio": 0.62, "advancers": 40, "decliners": 25},
        "sector_rotation": {"as_of": "2026-06-15", "leaders": ["Banking", "Consumer"], "laggards": ["Energy"]},
        "benchmark": {"strategies": [{"strategy": "bpjs"}, {"strategy": "bsjp"}]},
    }
    ex = mn._extract(data)
    assert ex["date"] == "2026-06-15"
    assert ex["bullish_ratio"] == 0.62
    assert ex["leading_sectors"] == ["Banking", "Consumer"]
    assert ex["lagging_sectors"] == ["Energy"]
    assert ex["best_strategy"] == "bpjs"


def test_extract_handles_empty():
    ex = mn._extract({})
    assert ex["date"] is None
    assert ex["best_strategy"] is None
    assert ex["leading_sectors"] == []


def test_model_importable():
    from app.db.models import MarketNarrative

    assert MarketNarrative.__tablename__ == "market_narratives"


# --------------------------------------------------------------------------- #
# Endpoint live (DB-gated)
# --------------------------------------------------------------------------- #
def test_endpoint_market_summary_live():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset.")
    from sqlalchemy import select, func
    from sqlalchemy.exc import OperationalError
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.models import MarketNarrative

    client = TestClient(app)
    try:
        r = client.get("/api/market-summary", params={"refresh": True})
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    if r.status_code == 404:
        pytest.skip("Data pasar belum tersedia.")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"].strip()
    assert body["disclaimer"]
    assert body["date"]
    # Narasi tersimpan ke market_narratives.
    from datetime import date as date_cls

    with SessionLocal() as db:
        row = db.scalar(
            select(func.count()).select_from(MarketNarrative).where(
                MarketNarrative.date == date_cls.fromisoformat(body["date"])
            )
        )
    assert row >= 1
