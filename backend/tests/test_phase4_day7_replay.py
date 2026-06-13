"""Phase 4 Day 7 — Market Replay Engine.

Sebagian besar butuh DB (auto-skip bila tak ada). Memilih tanggal historis yang
ramai kandidat secara dinamis agar tak bergantung tanggal hardcoded.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.quant import market_replay as mr
from app.quant.reconstruct import TECHNICAL_KEYS


def _db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test DB.")
    return SessionLocal()


def _busy_date(db):
    """Tanggal dengan kandidat replay terbanyak (untuk uji yang bermakna)."""
    from sqlalchemy import func, select

    from app.db.models import ReplayHistory

    row = db.execute(
        select(ReplayHistory.date, func.count())
        .group_by(ReplayHistory.date)
        .order_by(func.count().desc())
        .limit(1)
    ).first()
    return row[0] if row else None


def test_replay_date_range():
    db = _db()
    try:
        earliest, latest = mr.replay_date_range(db)
        assert earliest is not None and latest is not None
        assert earliest < latest
    finally:
        db.close()


def test_replay_on_busy_date_structure_and_sorting():
    db = _db()
    try:
        target = _busy_date(db)
        assert target is not None
        result = mr.replay_on_date(db, target, limit=10)

        assert result["date"] == target.isoformat()
        assert result["total_candidates"] > 0
        # Semua strategi teknikal hadir sebagai key (mungkin list kosong).
        assert set(result["strategies"]) == set(TECHNICAL_KEYS)

        for items in result["strategies"].values():
            assert len(items) <= 10
            # Urut turnover menurun.
            vals = [c["value"] or 0.0 for c in items]
            assert vals == sorted(vals, reverse=True)
            for c in items:
                assert set(c["ret"]) == {"1d", "3d", "7d", "30d"}
                assert c["price"] is not None
    finally:
        db.close()


def test_replay_empty_on_nontrading_date():
    db = _db()
    try:
        result = mr.replay_on_date(db, dt.date(1990, 1, 1))
        assert result["total_candidates"] == 0
        assert all(items == [] for items in result["strategies"].values())
    finally:
        db.close()


def test_replay_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    db = SessionLocal()
    try:
        target = _busy_date(db)
    finally:
        db.close()

    client = TestClient(app)
    r = client.get(f"/api/replay/{target.isoformat()}")
    assert r.status_code == 200
    body = r.json()
    assert body["date"] == target.isoformat()
    assert body["total_candidates"] > 0
    assert body["data_range"]["earliest"] and body["data_range"]["latest"]
    assert body["disclaimer"]

    # Format tanggal salah → 422.
    assert client.get("/api/replay/01-06-2025").status_code == 422
