"""Phase 4 Day 11 — Walk-Forward Backtesting.

Uji fungsi murni (grouping, metrik fold, konsistensi) + smoke DB/endpoint.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.quant import walk_forward as wf


def test_group_by_year_order():
    dates = [dt.date(2020, 3, 1), dt.date(2020, 9, 1), dt.date(2021, 2, 1)]
    grouped = wf._group_by_year(dates, [0.1, -0.05, 0.2])
    assert list(grouped.keys()) == [2020, 2021]
    assert grouped[2020] == [0.1, -0.05]
    assert grouped[2021] == [0.2]


def test_period_metrics():
    m = wf._period_metrics([0.10, -0.50, 0.10])
    assert m["annual_return"] == pytest.approx(1.10 * 0.50 * 1.10 - 1.0)
    assert m["max_drawdown"] == pytest.approx(-0.5)
    assert m["winrate"] == pytest.approx(2 / 3)
    assert m["n_periods"] == 3


def test_consistency_metrics():
    c = wf._consistency([0.1, -0.05, 0.2, 0.15])
    assert c["positive_year_ratio"] == pytest.approx(3 / 4)
    assert c["best_year"] == pytest.approx(0.2)
    assert c["worst_year"] == pytest.approx(-0.05)
    assert c["annual_return_std"] > 0


def test_consistency_empty():
    c = wf._consistency([])
    assert c["positive_year_ratio"] == 0.0
    assert c["best_year"] == 0.0


def test_walk_forward_structure_and_oos_consistency():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test DB.")

    db = SessionLocal()
    try:
        r = wf.walk_forward(db, "trend_following", min_train_years=1)
        assert r["mode"] == "anchored"
        assert len(r["folds"]) >= 5  # ~10 thn data → banyak fold

        # Fold kronologis: train_end < period.
        for f in r["folds"]:
            assert int(f["train_end"]) < int(f["period"])
            assert 0.0 <= f["winrate"] <= 1.0
            assert -1.0 <= f["max_drawdown"] <= 0.0

        oos = r["out_of_sample"]
        assert oos["total_years"] == len(r["folds"])
        assert 0.0 <= oos["consistency"]["positive_year_ratio"] <= 1.0
        # OOS = jahitan periode test; jumlah blok = total blok fold.
        assert oos["n_periods"] == sum(f["n_periods"] for f in r["folds"])
    finally:
        db.close()


def test_walkforward_endpoint_smoke():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    r = client.get("/api/walkforward/bpjs")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy"] == "bpjs"
    assert body["mode"] == "anchored"
    assert len(body["folds"]) >= 5
    assert "consistency" in body["out_of_sample"]
    assert body["disclaimer"]

    assert client.get("/api/walkforward/timeless").status_code == 404
    assert client.get("/api/walkforward/bpjs?hold=2").status_code == 422
