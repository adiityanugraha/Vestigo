"""Day 8 — Strategy Comparison Matrix.

Logika murni (assemble_matrix) diuji dengan baris sintetis; endpoint diuji
dengan TestClient memakai strategy_results sungguhan (auto-skip bila tak ada DB).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.strategy_matrix import assemble_matrix


@dataclass
class FakeResult:
    ticker: str
    strategy: str
    passed: bool


@dataclass
class FakeStock:
    name: str
    sector: str


KEYS = ["bsjp", "breakout", "high_growth", "timeless"]
STOCKS = {
    "BBCA": FakeStock("Bank Central Asia", "Banking"),
    "ANTM": FakeStock("Aneka Tambang", "Mining"),
}


def test_three_state_cells() -> None:
    # BBCA: lolos bsjp, gagal breakout, TIDAK ada baris fundamental (None).
    rows = [
        FakeResult("BBCA", "bsjp", True),
        FakeResult("BBCA", "breakout", False),
    ]
    matrix, universe = assemble_matrix(rows, STOCKS, KEYS, min_passed=1)
    assert universe == 1
    cells = matrix[0]["results"]
    assert cells["bsjp"] is True
    assert cells["breakout"] is False
    assert cells["high_growth"] is None  # tak dievaluasi -> None, bukan False
    assert cells["timeless"] is None
    assert matrix[0]["passed_count"] == 1
    assert matrix[0]["passed_strategies"] == ["bsjp"]


def test_min_passed_filter() -> None:
    rows = [
        FakeResult("BBCA", "bsjp", True),
        FakeResult("BBCA", "breakout", True),
        FakeResult("ANTM", "timeless", True),
    ]
    # min_passed=2 -> hanya BBCA (lolos 2), ANTM (lolos 1) tersaring.
    matrix, _ = assemble_matrix(rows, STOCKS, KEYS, min_passed=2)
    assert [m["ticker"] for m in matrix] == ["BBCA"]


def test_sorted_by_passed_count_then_ticker() -> None:
    rows = [
        FakeResult("ANTM", "high_growth", True),
        FakeResult("ANTM", "timeless", True),
        FakeResult("BBCA", "bsjp", True),
    ]
    matrix, _ = assemble_matrix(rows, STOCKS, KEYS, min_passed=1)
    assert [m["ticker"] for m in matrix] == ["ANTM", "BBCA"]  # 2 lolos di atas 1
    assert matrix[0]["passed_count"] == 2


def test_stock_metadata_attached() -> None:
    rows = [FakeResult("BBCA", "bsjp", True)]
    matrix, _ = assemble_matrix(rows, STOCKS, KEYS, min_passed=1)
    assert matrix[0]["name"] == "Bank Central Asia"
    assert matrix[0]["sector"] == "Banking"


def test_min_passed_zero_includes_all_failed() -> None:
    # min_passed=0 -> saham yang dinilai tapi gagal semua tetap muncul.
    rows = [FakeResult("BBCA", "bsjp", False), FakeResult("BBCA", "breakout", False)]
    matrix, universe = assemble_matrix(rows, STOCKS, KEYS, min_passed=0)
    assert universe == 1 and len(matrix) == 1
    assert matrix[0]["passed_count"] == 0


def test_unknown_ticker_metadata_none() -> None:
    rows = [FakeResult("XXXX", "bsjp", True)]
    matrix, _ = assemble_matrix(rows, {}, KEYS, min_passed=1)
    assert matrix[0]["name"] is None and matrix[0]["sector"] is None


# --------------------------------------------------------------------------- #
# Endpoint (butuh DB + strategy_results terisi)
# --------------------------------------------------------------------------- #
def _client_or_skip():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test endpoint.")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_api_strategy_matrix() -> None:
    client = _client_or_skip()
    resp = client.get("/api/strategy-matrix", params={"refresh": True, "min_passed": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert [s["key"] for s in data["strategies"]] == [
        "bsjp", "bpjs", "breakout", "trend_following", "potential_reversal",
        "high_growth", "cash_rich", "turnaround", "timeless",
    ]
    # Setiap baris matrix: passed_count cocok dgn jumlah sel True, & >= min_passed.
    for row in data["matrix"]:
        true_cells = [k for k, v in row["results"].items() if v is True]
        assert row["passed_count"] == len(true_cells) >= 1
        assert sorted(row["passed_strategies"]) == sorted(true_cells)
    # Terurut menurun berdasarkan passed_count.
    counts = [r["passed_count"] for r in data["matrix"]]
    assert counts == sorted(counts, reverse=True)
