"""Day 2 — Unit test strategi Breakout & Trend Following.

Memakai data sintetis deterministik: skenario lolos jelas, gagal per-kriteria,
dan data tidak cukup (NOT_EVALUATED). Helper Bar/make_bars dipinjam dari test
Day 1 agar konsisten.
"""

from __future__ import annotations

from app.core.strategies import registry
from app.core.strategies.base import StockData, StrategyType

from tests.test_day1_registry_regression import Bar, make_bars


def run(key: str, bars: list[Bar]):
    return registry.get(key).run(StockData(ticker="T", bars=bars))


# --------------------------------------------------------------------------- #
# Registry: 4 strategi teknikal kini terdaftar
# --------------------------------------------------------------------------- #
def test_breakout_and_trend_registered() -> None:
    keys = [s.key for s in registry.all_strategies()]
    assert {"breakout", "trend_following"} <= set(keys)
    for key in ("breakout", "trend_following"):
        assert registry.get(key).type is StrategyType.TECHNICAL


# --------------------------------------------------------------------------- #
# BREAKOUT
# --------------------------------------------------------------------------- #
def test_breakout_clear_pass() -> None:
    # 24 bar datar lalu lonjakan harga+volume di bar terakhir.
    closes = [1000.0] * 24 + [1050.0]
    volumes = [400_000_000.0] * 24 + [800_000_000.0]
    result = run("breakout", make_bars(closes, volumes))
    assert result.passed is True
    assert result.evaluated is True
    assert len(result.matched_criteria) == 5


def test_breakout_fails_low_liquidity() -> None:
    # Volume MA20 di bawah 300 juta -> kriteria likuiditas gagal.
    closes = [1000.0] * 24 + [1050.0]
    volumes = [100_000_000.0] * 24 + [150_000_000.0]
    result = run("breakout", make_bars(closes, volumes))
    assert result.passed is False
    assert result.criteria["volume_ma20_threshold"] is False
    # kriteria lain yang lolos tetap muncul di matched_criteria
    assert result.criteria["price_vs_previous"] is True


def test_breakout_fails_penny_stock() -> None:
    closes = [50.0] * 24 + [60.0]  # harga di bawah 100
    volumes = [400_000_000.0] * 24 + [800_000_000.0]
    result = run("breakout", make_bars(closes, volumes))
    assert result.passed is False
    assert result.criteria["price_above_100"] is False


def test_breakout_insufficient_bars() -> None:
    closes = [1000.0] * 10 + [1050.0]  # 11 bar < 20
    volumes = [400_000_000.0] * 11
    result = run("breakout", make_bars(closes, volumes))
    assert result.evaluated is False
    assert result.passed is False
    assert result.matched_criteria == []


# --------------------------------------------------------------------------- #
# TREND FOLLOWING
# --------------------------------------------------------------------------- #
def _rising_series(n: int = 250, base: float = 1000.0, step: float = 5.0):
    closes = [base + i * step for i in range(n)]
    volumes = [10_000_000.0] * n  # value = ~2200 * 10jt >> Rp1 miliar
    return make_bars(closes, volumes)


def test_trend_clear_pass() -> None:
    result = run("trend_following", _rising_series())
    assert result.passed is True
    assert result.evaluated is True
    assert len(result.matched_criteria) == 5


def test_trend_fails_downtrend() -> None:
    # Seri menurun -> MA20 < MA50 < ... , price < MA20.
    closes = [1000.0 + (250 - i) * 5.0 for i in range(250)]
    result = run("trend_following", make_bars(closes, [10_000_000.0] * 250))
    assert result.passed is False
    assert result.criteria["price_above_ma20"] is False
    assert result.criteria["ma20_above_ma50"] is False


def test_trend_fails_low_value() -> None:
    # Uptrend bagus tapi turnover < Rp1 miliar (volume kecil).
    closes = [1000.0 + i * 5.0 for i in range(250)]
    result = run("trend_following", make_bars(closes, [100.0] * 250))
    assert result.passed is False
    assert result.criteria["value_threshold"] is False
    assert result.criteria["ma20_above_ma50"] is True  # struktur tren tetap lolos


def test_trend_insufficient_bars() -> None:
    result = run("trend_following", _rising_series(n=150))  # < 200 -> MA200 None
    assert result.evaluated is False
    assert result.passed is False
    assert result.matched_criteria == []
