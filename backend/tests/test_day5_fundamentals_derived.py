"""Day 5 — Metrik turunan harga-sensitif + growth (tanpa DB/jaringan).

Memakai baris fundamentals & bar harga sintetis untuk menguji build_fundamental_view
dan helper growth (pct_change, cagr, growth_streak).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.core.fundamentals import (
    build_fundamental_view,
    cagr,
    derive_shares,
    growth_streak,
    pct_change,
)


@dataclass
class FakeRow:
    report_type: str
    period: str
    revenue: float | None = None
    net_income: float | None = None
    gross_profit: float | None = None
    income_from_operations: float | None = None
    common_equity: float | None = None
    cash_equivalents: float | None = None
    total_debt: float | None = None
    roe: float | None = None
    eps: float | None = None
    dps: float | None = None


@dataclass
class FakeBar:
    date: date
    close: float | None


def _bbca_rows() -> list[FakeRow]:
    annual = [
        FakeRow("ANNUAL", "2025", revenue=111.0, net_income=57.0),
        FakeRow("ANNUAL", "2024", revenue=107.0, net_income=54.0),
        FakeRow("ANNUAL", "2023", revenue=99.0, net_income=48.0),
        FakeRow("ANNUAL", "2022", revenue=86.0, net_income=40.0),
    ]
    ttm = FakeRow(
        "TTM", "TTM", revenue=108.0, net_income=57.0, gross_profit=106.0,
        common_equity=259.0, cash_equivalents=112.0, total_debt=2.7,
        roe=0.23, eps=471.22, dps=356.0,
    )
    return annual + [ttm]


# --------------------------------------------------------------------------- #
# Helper growth murni
# --------------------------------------------------------------------------- #
def test_pct_change() -> None:
    assert abs(pct_change(110, 100) - 10.0) < 1e-9
    assert abs(pct_change(90, 100) - (-10.0)) < 1e-9
    assert pct_change(100, 0) is None
    assert pct_change(None, 100) is None


def test_cagr() -> None:
    # 100 -> 133.1 dalam 3 tahun = 10% CAGR
    result = cagr(133.1, 100, 3)
    assert result is not None and abs(result - 10.0) < 0.01
    assert cagr(100, 0, 3) is None
    assert cagr(-5, 100, 3) is None  # nilai negatif tak valid untuk CAGR


def test_growth_streak() -> None:
    assert growth_streak([86, 99, 107, 111]) == 3   # naik terus
    assert growth_streak([86, 99, 95, 111]) == 1     # putus di tengah, hanya tahun terakhir
    assert growth_streak([100, 90, 80]) == 0         # menurun
    assert growth_streak([]) == 0


def test_derive_shares() -> None:
    assert abs(derive_shares(57.0, 471.22) - 57.0 / 471.22) < 1e-9
    assert derive_shares(57.0, 0) is None      # eps<=0
    assert derive_shares(-1.0, 471.22) is None  # net income negatif
    assert derive_shares(None, 10) is None


# --------------------------------------------------------------------------- #
# Builder lengkap
# --------------------------------------------------------------------------- #
def test_view_price_sensitive_metrics() -> None:
    view = build_fundamental_view("bbca", _bbca_rows(), close=5000.0, as_of=date(2026, 6, 10))
    shares = 57.0 / 471.22
    assert view.shares_outstanding == shares
    assert view.market_cap == 5000.0 * shares
    assert abs(view.pe_annualised - 5000.0 / 471.22) < 1e-9
    assert abs(view.pbv - (5000.0 * shares) / 259.0) < 1e-9
    assert abs(view.dividend_yield - 356.0 / 5000.0) < 1e-9
    assert view.date == "2026-06-10"


def test_view_growth_metrics() -> None:
    view = build_fundamental_view("bbca", _bbca_rows(), close=5000.0, as_of=date(2026, 6, 10))
    assert abs(view.revenue_growth_yoy - pct_change(111.0, 107.0)) < 1e-9
    assert abs(view.revenue_growth_3yr - cagr(111.0, 86.0, 3)) < 1e-9
    assert abs(view.net_income_growth_yoy - pct_change(57.0, 54.0)) < 1e-9
    assert view.sales_growth_streak == 3


def test_view_limited_fields_are_none() -> None:
    view = build_fundamental_view("bbca", _bbca_rows(), close=5000.0, as_of=date(2026, 6, 10))
    assert view.roe_5yr_avg is None
    assert view.dividend_streak is None


def test_view_price_return_from_bars() -> None:
    bars = [
        FakeBar(date(2024, 6, 10), 1000.0),
        FakeBar(date(2025, 6, 10), 1100.0),
        FakeBar(date(2026, 6, 10), 1200.0),
    ]
    view = build_fundamental_view("x", _bbca_rows(), close=1200.0, as_of=date(2026, 6, 10), price_bars=bars)
    assert abs(view.price_return - 20.0) < 1e-9  # 1000 -> 1200
    assert view.price_return_span_days == 730  # 2024-06-10 -> 2026-06-10


def test_view_loss_making_no_market_cap() -> None:
    # eps negatif -> shares None -> market_cap & pbv None, tapi growth tetap ada.
    rows = _bbca_rows()
    rows[-1].eps = -10.0  # baris TTM rugi
    view = build_fundamental_view("x", rows, close=5000.0, as_of=date(2026, 6, 10))
    assert view.shares_outstanding is None
    assert view.market_cap is None
    assert view.pbv is None
    assert view.pe_annualised is None
    assert view.sales_growth_streak == 3  # growth tak terpengaruh


def test_view_empty_rows() -> None:
    view = build_fundamental_view("x", [], close=5000.0, as_of=date(2026, 6, 10))
    assert view.market_cap is None
    assert view.revenue_growth_yoy is None
    assert view.sales_growth_streak == 0
    assert view.annual == []
