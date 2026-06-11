"""Day 6 — Strategi fundamental High Growth & Cash Rich (tanpa DB/jaringan).

Memakai FundamentalView sintetis + bar volume untuk menguji kriteria, termasuk
kasus fundamentals None (NOT_EVALUATED) dan bar < 20 (NOT_EVALUATED).
"""

from __future__ import annotations

from app.core.fundamentals import FundamentalView
from app.core.strategies import registry
from app.core.strategies.base import StockData, StrategyType

from tests.test_day1_registry_regression import Bar, make_bars


def run(key: str, bars, view):
    return registry.get(key).run(StockData(ticker="T", bars=bars, fundamentals=view))


def _bars(volume: float, n: int = 25):
    return make_bars([1000.0] * n, [volume] * n)


# --------------------------------------------------------------------------- #
# Registry: 7 strategi (5 teknikal + 2 fundamental)
# --------------------------------------------------------------------------- #
def test_fundamental_strategies_registered() -> None:
    keys = [s.key for s in registry.all_strategies()]
    # high_growth & cash_rich terdaftar setelah 5 strategi teknikal
    # (daftar lengkap 9 strategi dikunci oleh test Day 7).
    assert keys[5:7] == ["high_growth", "cash_rich"]
    assert registry.get("high_growth").type is StrategyType.FUNDAMENTAL
    assert registry.get("cash_rich").type is StrategyType.FUNDAMENTAL


# --------------------------------------------------------------------------- #
# HIGH GROWTH
# --------------------------------------------------------------------------- #
def test_high_growth_pass() -> None:
    view = FundamentalView(
        ticker="T",
        revenue_growth_3yr=15.0,
        revenue_growth_yoy=12.0,
        sales_growth_streak=3,
    )
    result = run("high_growth", _bars(5_000_000), view)
    assert result.passed is True
    assert len(result.matched_criteria) == 4


def test_high_growth_fails_low_3yr() -> None:
    view = FundamentalView(
        ticker="T", revenue_growth_3yr=8.0, revenue_growth_yoy=12.0, sales_growth_streak=3
    )
    result = run("high_growth", _bars(5_000_000), view)
    assert result.passed is False
    assert result.criteria["revenue_growth_3yr"] is False
    assert result.criteria["revenue_growth_yoy"] is True


def test_high_growth_none_growth_fails_not_crashes() -> None:
    # Data 3yr tak tersedia (None) -> kriteria False, bukan error.
    view = FundamentalView(
        ticker="T", revenue_growth_3yr=None, revenue_growth_yoy=12.0, sales_growth_streak=3
    )
    result = run("high_growth", _bars(5_000_000), view)
    assert result.evaluated is True
    assert result.passed is False
    assert result.criteria["revenue_growth_3yr"] is False


def test_high_growth_no_fundamentals_not_evaluated() -> None:
    result = run("high_growth", _bars(5_000_000), None)
    assert result.evaluated is False
    assert result.passed is False


def test_high_growth_insufficient_bars_not_evaluated() -> None:
    view = FundamentalView(ticker="T", revenue_growth_3yr=15.0, revenue_growth_yoy=12.0, sales_growth_streak=3)
    result = run("high_growth", _bars(5_000_000, n=10), view)  # < 20 bar
    assert result.evaluated is False


# --------------------------------------------------------------------------- #
# CASH RICH
# --------------------------------------------------------------------------- #
def _cash_rich_view(cash=80e12, market_cap=100e12, debt=10e12, pbv=1.5):
    return FundamentalView(
        ticker="T", cash_equivalents=cash, market_cap=market_cap, total_debt=debt, pbv=pbv
    )


def test_cash_rich_pass() -> None:
    # cash 80T >= 0.7*100T=70T ; debt 10T < 0.5*80T=40T ; pbv>0 ; mktcap>1M
    result = run("cash_rich", _bars(5_000_000), _cash_rich_view())
    assert result.passed is True
    assert len(result.matched_criteria) == 5


def test_cash_rich_fails_high_debt() -> None:
    result = run("cash_rich", _bars(5_000_000), _cash_rich_view(debt=50e12))
    assert result.passed is False
    assert result.criteria["debt_vs_cash"] is False


def test_cash_rich_fails_low_cash() -> None:
    result = run("cash_rich", _bars(5_000_000), _cash_rich_view(cash=50e12))
    assert result.passed is False
    assert result.criteria["cash_vs_market_cap"] is False


def test_cash_rich_none_market_cap_fails() -> None:
    # Saham rugi -> market_cap None -> kriteria terkait False, tak error.
    result = run("cash_rich", _bars(5_000_000), _cash_rich_view(market_cap=None))
    assert result.evaluated is True
    assert result.passed is False
    assert result.criteria["cash_vs_market_cap"] is False
    assert result.criteria["market_cap_min"] is False


def test_cash_rich_no_fundamentals_not_evaluated() -> None:
    result = run("cash_rich", _bars(5_000_000), None)
    assert result.evaluated is False
