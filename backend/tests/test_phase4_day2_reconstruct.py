"""Phase 4 Day 2 — rekonstruksi histori point-in-time (DB-free).

Fokus uji: jaminan ANTI LOOK-AHEAD. Evaluasi sebuah tanggal T harus IDENTIK
baik ketika bar setelah T ada (dengan nilai ekstrem) maupun tidak — membuktikan
strategi hanya melihat data <= T. Plus: hanya 5 strategi teknikal yang dijalankan
& only_passed menyaring baris gagal.
"""

from __future__ import annotations

import datetime as dt

from app.db.models import MarketData
from app.quant.reconstruct import (
    TECHNICAL_KEYS,
    get_technical_strategies,
    reconstruct_ticker,
)


def _make_bars(
    n: int = 260,
    start_close: float = 1000.0,
    step: float = 20.0,
    volume: int = 300_000,
    spike_from: int | None = None,
) -> list[MarketData]:
    """Uptrend linear sintetis (MA tersusun naik → trend_following bisa lolos).

    spike_from: bila diset, bar mulai indeks itu di-skala 10x (data "masa depan"
    ekstrem) untuk menguji bahwa ia TIDAK memengaruhi evaluasi tanggal sebelumnya.
    """
    bars: list[MarketData] = []
    base = dt.date(2020, 1, 1)
    prev = start_close
    for i in range(n):
        close = start_close + i * step
        if spike_from is not None and i >= spike_from:
            close *= 10.0
        high = max(prev, close) * 1.01
        low = min(prev, close) * 0.99
        bars.append(
            MarketData(
                ticker="TEST",
                date=base + dt.timedelta(days=i),
                open=prev,
                high=high,
                low=low,
                close=close,
                volume=volume,
                value=close * volume,
            )
        )
        prev = close
    return bars


def _norm(rows: list[dict]) -> list[tuple]:
    return sorted((r["date"].isoformat(), r["strategy"], r["passed"]) for r in rows)


def test_no_lookahead_future_bars_do_not_affect_past():
    strategies = get_technical_strategies()

    # Daftar penuh dengan lonjakan ekstrem mulai indeks 231 (masa depan dari T).
    full = _make_bars(260, spike_from=231)
    t = full[230].date

    # Versi terpotong tepat di T (tanpa bar masa depan sama sekali).
    truncated = _make_bars(231)

    _, _, rows_full = reconstruct_ticker(
        "TEST", full, strategies, end=t, only_passed=False
    )
    _, _, rows_trunc = reconstruct_ticker(
        "TEST", truncated, strategies, only_passed=False
    )

    assert rows_full, "harus ada evaluasi sampai tanggal T"
    assert _norm(rows_full) == _norm(rows_trunc)


def test_only_technical_strategies_present():
    strategies = get_technical_strategies()
    bars = _make_bars(260)
    _, _, rows = reconstruct_ticker("TEST", bars, strategies, only_passed=False)

    keys = {r["strategy"] for r in rows}
    assert keys, "harus ada minimal satu strategi yang dievaluasi"
    assert keys <= set(TECHNICAL_KEYS)
    # Tidak boleh ada strategi fundamental.
    for fundamental in ("high_growth", "turnaround", "timeless", "cash_rich"):
        assert fundamental not in keys


def test_only_passed_filters_failed_rows():
    strategies = get_technical_strategies()
    bars = _make_bars(260)

    _, passes, rows_passed = reconstruct_ticker(
        "TEST", bars, strategies, only_passed=True
    )
    assert all(r["passed"] for r in rows_passed)
    assert len(rows_passed) == passes

    _, _, rows_all = reconstruct_ticker("TEST", bars, strategies, only_passed=False)
    assert len(rows_all) >= len(rows_passed)
    assert any(not r["passed"] for r in rows_all), "uptrend harus punya sebagian gagal"


def test_date_window_filters():
    strategies = get_technical_strategies()
    bars = _make_bars(260)
    start = bars[230].date
    end = bars[240].date

    _, _, rows = reconstruct_ticker(
        "TEST", bars, strategies, start=start, end=end, only_passed=False
    )
    dates = {r["date"] for r in rows}
    assert dates, "rentang harus menghasilkan baris"
    assert min(dates) >= start
    assert max(dates) <= end


def test_uptrend_passes_trend_following():
    """Uptrend rapi pada bar terakhir harus lolos trend_following (sanity logika)."""
    strategies = get_technical_strategies()
    bars = _make_bars(260)
    t = bars[-1].date

    _, _, rows = reconstruct_ticker(
        "TEST", bars, strategies, start=t, end=t, only_passed=True
    )
    passed_keys = {r["strategy"] for r in rows}
    assert "trend_following" in passed_keys
