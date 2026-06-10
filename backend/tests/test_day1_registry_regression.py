"""Day 1 — Regression test Strategy Registry vs screener Phase 2.

Memastikan BSJP & BPJS yang dijalankan lewat registry menghasilkan keputusan
IDENTIK dengan jalur Phase 2 (app.core.screener.screen_bars):
  - dict criteria sama persis (key & nilai bool),
  - passed konsisten dengan ada/tidaknya kandidat screen_bars,
  - matched_criteria = tepat kriteria yang bernilai True,
  - data < MIN_BARS -> evaluated=False di registry, [] di screen_bars.

Diuji dengan skenario deterministik + 300 seri OHLCV acak (seed tetap).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pytest

from app.core import screener as screener_core
from app.core.strategies import registry
from app.core.strategies.base import StockData, StrategyType


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float


def make_bars(closes: list[float], volumes: list[float], opens: list[float] | None = None) -> list[Bar]:
    bars = []
    for i, close in enumerate(closes):
        open_ = opens[i] if opens else close * 0.99
        high = max(open_, close) * 1.01
        low = min(open_, close) * 0.99
        bars.append(Bar(open=open_, high=high, low=low, close=close, volume=volumes[i]))
    return bars


def random_bars(rng: random.Random, length: int) -> list[Bar]:
    """Seri acak yang kadang memicu lonjakan harga/volume agar dua sisi teruji."""
    closes, volumes, opens = [], [], []
    price = rng.uniform(100, 10_000)
    volume = rng.uniform(1e6, 5e8)
    for _ in range(length):
        # 15% kesempatan lonjakan besar (calon lolos), sisanya jalan normal.
        jump = rng.uniform(1.05, 1.15) if rng.random() < 0.15 else rng.uniform(0.95, 1.05)
        price = max(price * jump, 1.0)
        volume = max(volume * rng.uniform(0.5, 2.5), 1.0)
        opens.append(price * rng.uniform(0.97, 1.03))
        closes.append(price)
        volumes.append(volume)
    return make_bars(closes, volumes, opens)


# --------------------------------------------------------------------------- #
# Mekanika registry
# --------------------------------------------------------------------------- #
def test_registry_contains_bsjp_and_bpjs() -> None:
    keys = [s.key for s in registry.all_strategies()]
    assert keys == ["bsjp", "bpjs"]
    for strategy in registry.all_strategies():
        assert strategy.type is StrategyType.TECHNICAL
        meta = strategy.describe()
        assert set(meta) == {"key", "name", "type", "output_label"}


def test_register_duplicate_key_raises() -> None:
    from app.core.strategies.base import Strategy, StrategyResult

    class Fake(Strategy):
        key = "bsjp"  # bentrok dengan strategi terdaftar
        name = "Fake"
        type = StrategyType.TECHNICAL
        output_label = "Fake"

        def run(self, data: StockData) -> StrategyResult:  # pragma: no cover
            return StrategyResult(passed=False)

    with pytest.raises(ValueError, match="duplikat"):
        registry.register(Fake())


def test_load_defaults_idempotent() -> None:
    before = registry.all_strategies()
    registry.load_defaults()
    registry.load_defaults()
    assert registry.all_strategies() == before


# --------------------------------------------------------------------------- #
# Regression vs Phase 2
# --------------------------------------------------------------------------- #
def assert_identical_to_phase2(ticker: str, bars: list[Bar]) -> None:
    """Inti regression: bandingkan registry vs screen_bars untuk satu seri."""
    results = registry.run_all(StockData(ticker=ticker, bars=bars))
    phase2 = screener_core.screen_bars(ticker, bars)
    phase2_by_strategy = {c.strategy: c for c in phase2}
    inp = screener_core.build_screener_input(bars)

    for key, phase2_strategy in (("bsjp", "BSJP"), ("bpjs", "BPJS")):
        result = results[key]

        if inp is None:  # data < MIN_BARS
            assert result.evaluated is False
            assert result.passed is False
            assert phase2 == []
            continue

        expected_criteria = (
            screener_core.get_bsjp_criteria(inp, screener_core.MIN_DAILY_VALUE)
            if key == "bsjp"
            else screener_core.get_bpjs_criteria(inp, screener_core.MIN_DAILY_VALUE)
        )
        assert result.evaluated is True
        assert result.criteria == expected_criteria
        assert result.passed == all(expected_criteria.values())
        # passed harus konsisten dengan ada/tidaknya kandidat di jalur Phase 2.
        assert result.passed == (phase2_strategy in phase2_by_strategy)
        if result.passed:
            assert result.criteria == phase2_by_strategy[phase2_strategy].criteria
        # matched_criteria = tepat sebanyak kriteria True, tanpa template kosong.
        n_true = sum(expected_criteria.values())
        assert len(result.matched_criteria) == n_true
        assert all(isinstance(reason, str) and reason for reason in result.matched_criteria)


def test_insufficient_bars_not_evaluated() -> None:
    bars = make_bars([100, 101, 102], [1e6, 1e6, 1e6])  # < MIN_BARS (6)
    assert_identical_to_phase2("SHORT", bars)
    result = registry.get("bsjp").run(StockData(ticker="SHORT", bars=bars))
    assert result.evaluated is False and result.matched_criteria == []


def test_clear_pass_scenario() -> None:
    """Gap-up 8% + volume 2x + nilai transaksi besar -> lolos BSJP & BPJS."""
    closes = [1000.0] * 9 + [1080.0]
    volumes = [10_000_000.0] * 9 + [20_000_000.0]
    opens = [1000.0] * 9 + [1010.0]  # close >= open (syarat BPJS)
    bars = make_bars(closes, volumes, opens)

    results = registry.run_all(StockData(ticker="PASS", bars=bars))
    assert results["bsjp"].passed is True
    assert results["bpjs"].passed is True
    assert_identical_to_phase2("PASS", bars)


def test_clear_fail_scenario() -> None:
    """Harga flat & volume turun -> gagal kedua strategi."""
    closes = [1000.0] * 10
    volumes = [10_000_000.0] * 9 + [5_000_000.0]
    bars = make_bars(closes, volumes)

    results = registry.run_all(StockData(ticker="FAIL", bars=bars))
    assert results["bsjp"].passed is False
    assert results["bpjs"].passed is False
    assert_identical_to_phase2("FAIL", bars)


def test_random_series_identical_to_phase2() -> None:
    """300 seri acak deterministik, panjang 3..60 bar."""
    rng = random.Random(20260610)
    passed_count = 0
    for case in range(300):
        bars = random_bars(rng, length=rng.randint(3, 60))
        assert_identical_to_phase2(f"RND{case}", bars)
        results = registry.run_all(StockData(ticker=f"RND{case}", bars=bars))
        passed_count += sum(r.passed for r in results.values())
    # Sanity: skenario acak harus memuat kasus lolos DAN gagal (dua sisi teruji).
    assert passed_count > 0
