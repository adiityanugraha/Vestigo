"""Phase 4 Day 3 — return forward & trade log.

Fokus uji: kebenaran matematika return forward (offset hari bursa, biaya
round-trip, penanganan jatuh tempo/None) + smoke test materialisasi
replay_history bila DB tersedia.
"""

from __future__ import annotations

import pytest

from app.quant.forward_returns import (
    DEFAULT_ROUND_TRIP_COST,
    FORWARD_HORIZONS,
    build_replay_history,
    compute_forward_returns,
    load_return_series,
)


def test_forward_returns_basic_and_cost():
    # close naik 10 per hari dari 100.
    closes = [100.0 + 10.0 * i for i in range(40)]  # 100,110,...,490
    rets = compute_forward_returns(closes, j=0, cost=0.0)
    assert rets[1] == pytest.approx(110 / 100 - 1)
    assert rets[3] == pytest.approx(130 / 100 - 1)
    assert rets[7] == pytest.approx(170 / 100 - 1)
    assert rets[30] == pytest.approx(400 / 100 - 1)


def test_cost_is_subtracted_uniformly():
    closes = [100.0 + 10.0 * i for i in range(40)]
    gross = compute_forward_returns(closes, j=0, cost=0.0)
    net = compute_forward_returns(closes, j=0, cost=0.01)
    for h in FORWARD_HORIZONS:
        assert net[h] == pytest.approx(gross[h] - 0.01)


def test_immature_horizons_are_none():
    closes = [100.0 + i for i in range(10)]  # indeks 0..9
    # dari indeks 8: +1 ada (idx9), +3/+7/+30 di luar seri -> None.
    rets = compute_forward_returns(closes, j=8)
    assert rets[1] == pytest.approx((109 / 108 - 1) - DEFAULT_ROUND_TRIP_COST)
    assert rets[3] is None
    assert rets[7] is None
    assert rets[30] is None


def test_invalid_entry_price_returns_none():
    closes = [0.0, 110.0, 120.0]
    rets = compute_forward_returns(closes, j=0)
    assert all(v is None for v in rets.values())


def test_trading_day_offset_not_calendar():
    # Offset adalah indeks bar, bukan kalender — bar berurutan = hari bursa.
    closes = [10.0, 11.0, 12.0, 13.0, 14.0]
    rets = compute_forward_returns(closes, j=1, horizons=(1, 3), cost=0.0)
    assert rets[1] == pytest.approx(12 / 11 - 1)   # bar berikutnya
    assert rets[3] == pytest.approx(14 / 11 - 1)   # 3 bar setelahnya


def test_build_replay_history_smoke():
    """Materialisasi nyata untuk 1 ticker bila DB tersedia (else skip)."""
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati smoke test DB.")

    db = SessionLocal()
    try:
        summary = build_replay_history(
            db, tickers=["BBCA"], persist=True, progress=False
        )
        # BBCA pasti punya kandidat lolos dari rekonstruksi Day 2.
        assert summary["trades"] > 0
        assert summary["persisted"] == summary["trades"]
        assert summary["matured_1d"] > 0

        # Return series harus terbentuk & nilai wajar (bukan NaN/None).
        series = load_return_series(db, "bsjp", horizon=1)
        assert series, "harus ada trade bsjp yang jatuh tempo"
        for d, r in series[:20]:
            assert isinstance(r, float)
            assert -0.9 < r < 5.0  # batas sanity longgar
    finally:
        db.close()
