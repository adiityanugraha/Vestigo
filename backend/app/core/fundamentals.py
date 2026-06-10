"""Komputasi metrik fundamental turunan (Phase 3 Day 5).

Dua kelas metrik:
  1. HARGA-SENSITIF (refresh harian -> tabel fundamental_derived):
       - market_cap     = close * shares
       - pe_annualised  = close / eps
       - pbv            = market_cap / common_equity
       - dividend_yield = dps / close
     shares diturunkan dari net_income_ttm / eps (terbukti akurat ~1% vs nilai
     Yahoo; tak butuh kolom shares baru). Bila eps<=0 -> shares None, sehingga
     market_cap & pbv None (saham rugi memang gugur di kriteria berbasis PE).

  2. GROWTH (dihitung ON-THE-FLY dari baris ANNUAL, seperti MA teknikal):
       - revenue/net_income growth YoY & 3-tahun (CAGR)
       - sales_growth_streak (tahun beruntun revenue naik)

  TERBATAS oleh data Yahoo gratis (lihat data/fundamentals_fetch.py):
       - roe_5yr_avg, dividend_streak -> None (histori tak tersedia)
       - price_return: dihitung atas histori market_data yang ADA (mis. ~2thn),
         disertai span hari -> Timeless "10yr return" jadi proxy terbatas.

Modul murni (tanpa DB); pemanggil menyuplai baris fundamentals + harga.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls


# --------------------------------------------------------------------------- #
# Helper growth (murni, mudah diuji)
# --------------------------------------------------------------------------- #
def pct_change(new: float | None, old: float | None) -> float | None:
    """Perubahan persen YoY. None bila old kosong/<=0 atau new kosong."""
    if new is None or old is None or old <= 0:
        return None
    return (new / old - 1) * 100


def cagr(new: float | None, old: float | None, years: int) -> float | None:
    """Compound annual growth rate (persen) selama `years` tahun."""
    if new is None or old is None or old <= 0 or new <= 0 or years <= 0:
        return None
    return ((new / old) ** (1 / years) - 1) * 100


def growth_streak(values_oldest_first: list[float | None]) -> int:
    """Jumlah tahun beruntun (paling baru ke belakang) yang nilainya NAIK."""
    streak = 0
    for i in range(len(values_oldest_first) - 1, 0, -1):
        cur, prev = values_oldest_first[i], values_oldest_first[i - 1]
        if cur is not None and prev is not None and cur > prev:
            streak += 1
        else:
            break
    return streak


# --------------------------------------------------------------------------- #
# Struktur data
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AnnualPoint:
    period: str
    revenue: float | None
    net_income: float | None


@dataclass(frozen=True)
class FundamentalView:
    ticker: str

    # --- Raw (dari tabel fundamentals, baris TTM) ---
    revenue_ttm: float | None = None
    net_income_ttm: float | None = None
    gross_profit: float | None = None
    income_from_operations: float | None = None
    common_equity: float | None = None
    cash_equivalents: float | None = None
    total_debt: float | None = None
    roe: float | None = None
    eps: float | None = None
    dps: float | None = None

    annual: list[AnnualPoint] = field(default_factory=list)

    # --- Harga-sensitif (derived harian) ---
    close: float | None = None
    date: str | None = None
    shares_outstanding: float | None = None
    market_cap: float | None = None
    pe_annualised: float | None = None
    pbv: float | None = None
    dividend_yield: float | None = None

    # --- Growth (on-the-fly) ---
    revenue_growth_yoy: float | None = None
    revenue_growth_3yr: float | None = None
    net_income_growth_yoy: float | None = None
    net_income_growth_3yr: float | None = None
    sales_growth_streak: int = 0

    # --- Terbatas / tak tersedia ---
    roe_5yr_avg: float | None = None
    dividend_streak: int | None = None
    price_return: float | None = None
    price_return_span_days: int | None = None


# --------------------------------------------------------------------------- #
# Builder
# --------------------------------------------------------------------------- #
class _FundRow:
    """Protokol minimal untuk baris ORM Fundamental yang dipakai builder."""

    report_type: str
    period: str
    revenue: float | None
    net_income: float | None
    gross_profit: float | None
    income_from_operations: float | None
    common_equity: float | None
    cash_equivalents: float | None
    total_debt: float | None
    roe: float | None
    eps: float | None
    dps: float | None


def derive_shares(net_income_ttm: float | None, eps: float | None) -> float | None:
    """shares = net_income / eps (hanya untuk eps>0 & net_income>0)."""
    if eps is None or eps <= 0 or net_income_ttm is None or net_income_ttm <= 0:
        return None
    return net_income_ttm / eps


def build_fundamental_view(
    ticker: str,
    rows: list,
    close: float | None = None,
    as_of: date_cls | None = None,
    price_bars: list | None = None,
) -> FundamentalView:
    """Rakit FundamentalView dari baris fundamentals + harga terkini.

    rows       : baris ORM Fundamental (campuran ANNUAL & TTM) untuk satu ticker.
    close      : harga penutupan terbaru (untuk metrik harga-sensitif).
    as_of      : tanggal harga (untuk fundamental_derived.date).
    price_bars : opsional, bar market_data urut kronologis (untuk price_return).
    """
    ttm = next((r for r in rows if r.report_type == "TTM"), None)
    annual_rows = sorted(
        (r for r in rows if r.report_type == "ANNUAL"),
        key=lambda r: r.period,
        reverse=True,
    )  # terbaru dulu
    annual = [
        AnnualPoint(period=r.period, revenue=r.revenue, net_income=r.net_income)
        for r in annual_rows
    ]

    # --- Growth dari histori tahunan ---
    rev_yoy = rev_3yr = ni_yoy = ni_3yr = None
    streak = 0
    if len(annual) >= 2:
        rev_yoy = pct_change(annual[0].revenue, annual[1].revenue)
        ni_yoy = pct_change(annual[0].net_income, annual[1].net_income)
    if len(annual) >= 4:
        rev_3yr = cagr(annual[0].revenue, annual[3].revenue, 3)
        ni_3yr = cagr(annual[0].net_income, annual[3].net_income, 3)
    if annual:
        revenues_oldest_first = [a.revenue for a in reversed(annual)]
        streak = growth_streak(revenues_oldest_first)

    # --- Metrik harga-sensitif ---
    eps = ttm.eps if ttm else None
    dps = ttm.dps if ttm else None
    common_equity = ttm.common_equity if ttm else None
    net_income_ttm = ttm.net_income if ttm else None

    shares = derive_shares(net_income_ttm, eps)
    market_cap = (close * shares) if (close and shares) else None
    pe = (close / eps) if (close and eps and eps > 0) else None
    pbv = (market_cap / common_equity) if (market_cap and common_equity and common_equity > 0) else None
    div_yield = (dps / close) if (close and dps) else None

    # --- Price return atas histori yang tersedia ---
    price_return = price_span = None
    if price_bars:
        first = next((b for b in price_bars if b.close), None)
        last = next((b for b in reversed(price_bars) if b.close), None)
        if first and last and first.close:
            price_return = (last.close / first.close - 1) * 100
            price_span = (last.date - first.date).days

    return FundamentalView(
        ticker=ticker.strip().upper(),
        revenue_ttm=ttm.revenue if ttm else None,
        net_income_ttm=net_income_ttm,
        gross_profit=ttm.gross_profit if ttm else None,
        income_from_operations=ttm.income_from_operations if ttm else None,
        common_equity=common_equity,
        cash_equivalents=ttm.cash_equivalents if ttm else None,
        total_debt=ttm.total_debt if ttm else None,
        roe=ttm.roe if ttm else None,
        eps=eps,
        dps=dps,
        annual=annual,
        close=close,
        date=as_of.isoformat() if as_of else None,
        shares_outstanding=shares,
        market_cap=market_cap,
        pe_annualised=pe,
        pbv=pbv,
        dividend_yield=div_yield,
        revenue_growth_yoy=rev_yoy,
        revenue_growth_3yr=rev_3yr,
        net_income_growth_yoy=ni_yoy,
        net_income_growth_3yr=ni_3yr,
        sales_growth_streak=streak,
        roe_5yr_avg=None,       # histori 5thn tak tersedia (Yahoo gratis)
        dividend_streak=None,   # streak dividen tak tersedia
        price_return=price_return,
        price_return_span_days=price_span,
    )
