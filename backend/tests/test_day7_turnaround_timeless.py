"""Day 7 — Strategi Turnaround & Timeless + registry lengkap 9 strategi.

Kebijakan "proxy + lewati, ditandai" diuji eksplisit:
  - kriteria tanpa data struktural -> masuk skipped_criteria, TIDAK menggagalkan;
  - kriteria proxy (RoE saat ini, return span tersedia) dievaluasi & berlabel;
  - bila data IFO tersedia (sumber di-upgrade), kriteria Turnaround b & g aktif.
"""

from __future__ import annotations

from app.core.fundamentals import AnnualPoint, FundamentalView
from app.core.strategies import registry
from app.core.strategies.base import StockData, StrategyType

from tests.test_day1_registry_regression import make_bars


def run(key: str, bars, view):
    return registry.get(key).run(StockData(ticker="T", bars=bars, fundamentals=view))


def _bars(close: float = 1000.0, volume: float = 10_000_000.0, n: int = 25):
    # value per bar = close*volume; default 10 miliar -> lolos Value MA20 >= 5M.
    return make_bars([close] * n, [volume] * n)


# --------------------------------------------------------------------------- #
# Registry lengkap
# --------------------------------------------------------------------------- #
def test_all_nine_strategies_registered() -> None:
    keys = [s.key for s in registry.all_strategies()]
    assert keys == [
        "bsjp", "bpjs", "breakout", "trend_following", "potential_reversal",
        "high_growth", "cash_rich", "turnaround", "timeless",
    ]
    fundamental = registry.by_type(StrategyType.FUNDAMENTAL)
    assert [s.key for s in fundamental] == [
        "high_growth", "cash_rich", "turnaround", "timeless",
    ]


# --------------------------------------------------------------------------- #
# TURNAROUND
# --------------------------------------------------------------------------- #
def _turnaround_view(**overrides) -> FundamentalView:
    base = dict(
        ticker="T",
        net_income_growth_yoy=8.0,
        revenue_growth_yoy=6.0,
        pbv=0.9,
        pe_annualised=7.5,
    )
    base.update(overrides)
    return FundamentalView(**base)


def test_turnaround_pass_with_skipped_marked() -> None:
    result = run("turnaround", _bars(), _turnaround_view())
    assert result.evaluated is True
    assert result.passed is True
    # 5 kriteria terhitung lolos semua; 3 dilewati (IFO x2 + PE annualised).
    assert len(result.criteria) == 5
    assert len(result.skipped_criteria) == 3
    assert any("pe_annualised" in s for s in result.skipped_criteria)
    assert any("income_from_operations" in s.lower() for s in result.skipped_criteria)


def test_turnaround_fails_expensive_pe() -> None:
    result = run("turnaround", _bars(), _turnaround_view(pe_annualised=15.0))
    assert result.passed is False
    assert result.criteria["pe_max_12"] is False


def test_turnaround_fails_negative_growth() -> None:
    result = run("turnaround", _bars(), _turnaround_view(net_income_growth_yoy=-3.0))
    assert result.passed is False
    assert result.criteria["net_income_growth_yoy"] is False


def test_turnaround_ifo_criteria_activate_when_data_present() -> None:
    # Bila IFO tersedia (mis. sumber data di-upgrade), kriteria b & g aktif.
    view = _turnaround_view(
        net_income_ttm=50.0, income_from_operations=60.0, gross_profit=100.0
    )
    result = run("turnaround", _bars(), view)
    assert "net_income_vs_ifo" in result.criteria
    assert "ifo_vs_gross_profit" in result.criteria
    assert result.criteria["net_income_vs_ifo"] is True   # 50 <= 60
    assert result.criteria["ifo_vs_gross_profit"] is True  # 60 <= 100
    # hanya PE annualised yang tetap dilewati
    assert len(result.skipped_criteria) == 1
    assert result.passed is True


def test_turnaround_no_fundamentals_not_evaluated() -> None:
    result = run("turnaround", _bars(), None)
    assert result.evaluated is False


# --------------------------------------------------------------------------- #
# TIMELESS
# --------------------------------------------------------------------------- #
def _timeless_view(**overrides) -> FundamentalView:
    base = dict(
        ticker="T",
        roe=0.18,  # 18% (fraksi) -> proxy RoE
        net_income_growth_3yr=4.0,
        annual=[AnnualPoint(period="2025", revenue=100e12, net_income=2e12)],
        price_return=35.0,
        price_return_span_days=730,
        pe_annualised=12.0,
        common_equity=50e12,
        dividend_yield=0.03,  # 3% (fraksi)
    )
    base.update(overrides)
    return FundamentalView(**base)


def test_timeless_pass_with_proxy_labels() -> None:
    result = run("timeless", _bars(), _timeless_view())
    assert result.evaluated is True
    assert result.passed is True
    assert len(result.criteria) == 9  # 10 kriteria blueprint - 1 dilewati (streak)
    assert len(result.skipped_criteria) == 1
    assert "dividend_streak" in result.skipped_criteria[0]
    # label proxy muncul di deskripsi RoE & price return
    assert any("proxy RoE saat ini" in m for m in result.matched_criteria)
    assert any("proxy 10-Year" in m for m in result.matched_criteria)


def test_timeless_uses_real_5yr_roe_when_available() -> None:
    # Bila roe_5yr_avg tersedia, dipakai tanpa label proxy.
    result = run("timeless", _bars(), _timeless_view(roe_5yr_avg=15.0))
    assert result.criteria["roe_min_10"] is True
    roe_desc = [m for m in result.matched_criteria if m.startswith("RoE")][0]
    assert "proxy" not in roe_desc


def test_timeless_fails_low_roe() -> None:
    result = run("timeless", _bars(), _timeless_view(roe=0.06))  # 6% < 10%
    assert result.passed is False
    assert result.criteria["roe_min_10"] is False


def test_timeless_fails_small_net_income() -> None:
    view = _timeless_view(annual=[AnnualPoint(period="2025", revenue=1e12, net_income=0.5e12)])
    result = run("timeless", _bars(), view)
    assert result.passed is False
    assert result.criteria["net_income_annual_min"] is False


def test_timeless_fails_no_dividend() -> None:
    result = run("timeless", _bars(), _timeless_view(dividend_yield=None))
    assert result.passed is False
    assert result.criteria["dividend_yield_min"] is False


def test_timeless_fails_illiquid() -> None:
    # value per bar = 1000 * 1000 = 1 juta << 5 miliar.
    result = run("timeless", _bars(volume=1_000.0), _timeless_view())
    assert result.passed is False
    assert result.criteria["value_ma20_min"] is False


def test_timeless_no_fundamentals_not_evaluated() -> None:
    result = run("timeless", _bars(), None)
    assert result.evaluated is False
