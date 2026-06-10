"""Day 4 — Parsing & persistensi data fundamental (tanpa jaringan).

Memakai payload quoteSummary sintetis yang meniru struktur Yahoo (termasuk kasus
field IDX yang None/0) untuk menguji parse_summary_result + snapshot_to_rows tanpa
memanggil Yahoo. Test live (DB/jaringan) sengaja tidak disertakan agar suite
deterministik & cepat.
"""

from __future__ import annotations

from app.data.fundamentals_fetch import (
    FundamentalSnapshot,
    parse_summary_result,
    snapshot_to_rows,
)


def _wrap(x: float) -> dict:
    return {"raw": x, "fmt": str(x)}


# Payload meniru bentuk Yahoo: agregat TTM andal, histori tahunan andal,
# operatingIncome & grossProfit per-tahun None/0 (khas IDX).
SAMPLE_RESULT = {
    "financialData": {
        "totalRevenue": _wrap(108_629_000_000_000),
        "grossProfits": _wrap(106_232_000_000_000),
        "operatingIncome": _wrap(0),  # sering 0 untuk IDX -> harus jadi None
        "returnOnEquity": _wrap(0.2297),
        "totalCash": _wrap(112_486_000_000_000),
        "totalDebt": _wrap(2_733_000_000_000),
    },
    "summaryDetail": {
        "marketCap": _wrap(678_891_000_000_000),
        "trailingPE": _wrap(11.72),
        "dividendYield": _wrap(0.0691),
        "dividendRate": _wrap(356.0),
        "priceToBook": None,  # summaryDetail kosong -> fallback ke keyStats
    },
    "defaultKeyStatistics": {
        "trailingEps": _wrap(471.22),
        "priceToBook": _wrap(2.6199),
    },
    "incomeStatementHistory": {
        "incomeStatementHistory": [
            {"endDate": {"fmt": "2025-12-31"}, "totalRevenue": _wrap(111_861_000_000_000),
             "netIncome": _wrap(57_537_000_000_000), "grossProfit": _wrap(0),
             "operatingIncome": None},
            {"endDate": {"fmt": "2024-12-31"}, "totalRevenue": _wrap(107_896_000_000_000),
             "netIncome": _wrap(54_836_000_000_000)},
            {"endDate": {"fmt": "2023-12-31"}, "totalRevenue": _wrap(99_945_000_000_000),
             "netIncome": _wrap(48_639_000_000_000)},
            {"endDate": {"fmt": "2022-12-31"}, "totalRevenue": _wrap(86_770_000_000_000),
             "netIncome": _wrap(40_735_000_000_000)},
        ]
    },
}


def test_parse_ttm_aggregates() -> None:
    snap = parse_summary_result("bbca", SAMPLE_RESULT)
    assert snap.ticker == "BBCA"
    assert snap.revenue_ttm == 108_629_000_000_000
    assert snap.gross_profit_ttm == 106_232_000_000_000
    assert snap.cash_equivalents == 112_486_000_000_000
    assert snap.total_debt == 2_733_000_000_000
    assert snap.roe == 0.2297
    assert snap.eps == 471.22
    assert snap.dps == 356.0
    assert snap.trailing_pe == 11.72
    assert snap.dividend_yield == 0.0691


def test_unreliable_fields_become_none() -> None:
    snap = parse_summary_result("bbca", SAMPLE_RESULT)
    # operatingIncome=0 -> None (Yahoo IDX kerap kosong)
    assert snap.income_from_operations is None


def test_pbv_fallback_and_common_equity_derivation() -> None:
    snap = parse_summary_result("bbca", SAMPLE_RESULT)
    # PBV diambil dari defaultKeyStatistics karena summaryDetail None.
    assert snap.pbv == 2.6199
    # common_equity = marketCap / PBV
    assert snap.common_equity is not None
    assert abs(snap.common_equity - 678_891_000_000_000 / 2.6199) < 1e6


def test_annual_history_parsed_in_order() -> None:
    snap = parse_summary_result("bbca", SAMPLE_RESULT)
    assert [r.period for r in snap.annual] == ["2025", "2024", "2023", "2022"]
    assert snap.annual[0].net_income == 57_537_000_000_000
    assert snap.annual[-1].revenue == 86_770_000_000_000


def test_snapshot_to_rows_shape() -> None:
    snap = parse_summary_result("bbca", SAMPLE_RESULT)
    rows = snapshot_to_rows(snap)
    # 4 ANNUAL + 1 TTM
    assert len(rows) == 5
    annual = [r for r in rows if r["report_type"] == "ANNUAL"]
    ttm = [r for r in rows if r["report_type"] == "TTM"]
    assert len(annual) == 4 and len(ttm) == 1

    # ANNUAL hanya membawa revenue & net_income; agregat neraca None.
    for row in annual:
        assert row["revenue"] is not None
        assert row["net_income"] is not None
        assert row["cash_equivalents"] is None
        assert row["gross_profit"] is None

    # TTM membawa agregat; net_income TTM = net income tahun terbaru.
    t = ttm[0]
    assert t["period"] == "TTM"
    assert t["cash_equivalents"] == 112_486_000_000_000
    assert t["common_equity"] is not None
    assert t["net_income"] == 57_537_000_000_000
    assert t["dividend_streak"] is None  # tak tersedia dari Yahoo


def test_empty_result_safe() -> None:
    snap = parse_summary_result("xxxx", {})
    assert snap.annual == []
    assert snap.revenue_ttm is None
    assert snap.common_equity is None
    rows = snapshot_to_rows(snap)
    # Tetap menghasilkan 1 baris TTM (semua None) meski tanpa histori.
    assert len(rows) == 1 and rows[0]["report_type"] == "TTM"
    assert rows[0]["net_income"] is None


def test_snapshot_default_construct() -> None:
    # Dataclass bisa dibuat minimal (dipakai test lain / fallback).
    snap = FundamentalSnapshot(ticker="ZZ")
    assert snap.annual == [] and snap.revenue_ttm is None
