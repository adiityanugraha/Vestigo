"""Phase 4 Day 9 — Correlation Matrix.

Sebagian besar butuh DB (auto-skip). Memverifikasi struktur matriks, simetri,
diagonal 1, pasangan unik a<b, dan endpoint.
"""

from __future__ import annotations

import pytest

from app.quant import correlation_matrix as cm


def _db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test DB.")
    return SessionLocal()


def test_resolve_universe_lq45_subset_of_available():
    db = _db()
    try:
        lq = cm.resolve_universe(db, "lq45")
        allu = set(cm.resolve_universe(db, "all"))
        assert 10 <= len(lq) <= 46
        assert set(lq) <= allu  # selalu intersect ketersediaan
    finally:
        db.close()


def test_resolve_universe_invalid():
    db = _db()
    try:
        with pytest.raises(ValueError):
            cm.resolve_universe(db, "ngawur")
    finally:
        db.close()


def test_correlation_matrix_properties():
    db = _db()
    try:
        result = cm.compute_correlation(db, universe="lq45", window=90, persist=True)
        tickers = result["tickers"]
        matrix = result["matrix"]
        n = len(tickers)
        assert n >= 2
        assert len(matrix) == n and all(len(row) == n for row in matrix)

        # Diagonal = 1, simetris, nilai dalam [-1, 1].
        for i in range(n):
            assert matrix[i][i] == pytest.approx(1.0, abs=1e-6)
            for j in range(n):
                assert -1.0001 <= matrix[i][j] <= 1.0001
                assert matrix[i][j] == pytest.approx(matrix[j][i], abs=1e-6)

        # Pasangan unik a<b, jumlah = n*(n-1)/2.
        assert len(result["pairs"]) == n * (n - 1) // 2
        for p in result["pairs"]:
            assert p["ticker_a"] < p["ticker_b"]
    finally:
        db.close()


def test_pairs_persisted():
    db = _db()
    try:
        cm.compute_correlation(db, universe="lq45", window=90, persist=True)
        from sqlalchemy import func, select

        from app.db.models import CorrelationMatrix

        count = db.scalar(
            select(func.count()).select_from(CorrelationMatrix).where(
                CorrelationMatrix.window == "90d"
            )
        )
        assert count and count > 0
    finally:
        db.close()


def test_correlation_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    r = client.get("/api/correlation?universe=lq45&window=90")
    assert r.status_code == 200
    body = r.json()
    assert body["universe"] == "lq45"
    assert body["window"] == "90d"
    assert body["n"] == len(body["tickers"]) == len(body["matrix"])
    assert len(body["top_correlated"]) > 0
    assert body["disclaimer"]

    assert client.get("/api/correlation?universe=ngawur").status_code == 422
    assert client.get("/api/correlation?window=5").status_code == 422  # < 20
