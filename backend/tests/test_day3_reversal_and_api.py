"""Day 3 — Potential Reversal strategy + endpoint /api/strategies & ?strategy=.

Unit test reversal pakai data sintetis. Endpoint diuji dengan FastAPI TestClient
memakai DB & registry sungguhan (read-only: tidak menulis market_data). Bila
DATABASE_URL tidak diset, test endpoint di-skip otomatis.
"""

from __future__ import annotations

import pytest

from app.core.strategies import registry
from app.core.strategies.base import StockData, StrategyType

from tests.test_day1_registry_regression import Bar, make_bars


def run(key: str, bars: list[Bar]):
    return registry.get(key).run(StockData(ticker="T", bars=bars))


# --------------------------------------------------------------------------- #
# Registry: 5 strategi teknikal kini terdaftar
# --------------------------------------------------------------------------- #
def test_five_technical_strategies_registered() -> None:
    keys = [s.key for s in registry.all_strategies()]
    assert keys == ["bsjp", "bpjs", "breakout", "trend_following", "potential_reversal"]
    assert all(s.type is StrategyType.TECHNICAL for s in registry.all_strategies())


# --------------------------------------------------------------------------- #
# POTENTIAL REVERSAL
# --------------------------------------------------------------------------- #
def _reversal_pass_bars() -> list[Bar]:
    """Harga turun stabil (membentuk MA20 > MA10 > harga di area koreksi), lalu
    bar terakhir menembus naik di atas MA10 dengan volume di atas MA20.

    Konstruksi: 20 bar menurun dari 1200 -> 1010, bar terakhir loncat ke 1070
    (di atas MA10 ~1052, tapi masih di bawah MA20 ~1098), volume tinggi.
    """
    closes = [1200.0 - i * 10 for i in range(20)]  # 1200..1010 menurun
    closes.append(1070.0)  # bar reversal: naik dari 1010, tetap di bawah MA20
    volumes = [1_000_000.0] * 20 + [5_000_000.0]
    return make_bars(closes, volumes)


def test_reversal_clear_pass() -> None:
    result = run("potential_reversal", _reversal_pass_bars())
    assert result.evaluated is True
    assert result.passed is True
    assert len(result.matched_criteria) == 6


def test_reversal_fails_in_uptrend() -> None:
    # Uptrend mulus: harga di atas MA20, prev tidak di bawah MA10 -> gagal.
    closes = [1000.0 + i * 10 for i in range(21)]
    result = run("potential_reversal", make_bars(closes, [2_000_000.0] * 21))
    assert result.passed is False
    assert result.criteria["ma20_above_price"] is False


def test_reversal_fails_low_volume() -> None:
    bars = _reversal_pass_bars()
    # Turunkan volume bar terakhir di bawah rata-rata -> kriteria volume gagal.
    last = bars[-1]
    bars[-1] = Bar(last.open, last.high, last.low, last.close, 100_000.0)
    result = run("potential_reversal", bars)
    assert result.passed is False
    assert result.criteria["volume_above_ma20"] is False


def test_reversal_insufficient_bars() -> None:
    closes = [1000.0 - i * 10 for i in range(10)] + [1100.0]  # 11 bar < 20
    result = run("potential_reversal", make_bars(closes, [1_000_000.0] * 11))
    assert result.evaluated is False
    assert result.passed is False


# --------------------------------------------------------------------------- #
# Endpoint API (butuh DB)
# --------------------------------------------------------------------------- #
def _client_or_skip():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test endpoint.")
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_api_list_strategies() -> None:
    client = _client_or_skip()
    resp = client.get("/api/strategies")
    assert resp.status_code == 200
    data = resp.json()
    keys = [s["key"] for s in data]
    assert keys == ["bsjp", "bpjs", "breakout", "trend_following", "potential_reversal"]
    for item in data:
        assert set(item) == {"key", "name", "type", "output_label"}
        assert item["type"] in ("technical", "fundamental")


def test_api_screener_single_strategy() -> None:
    client = _client_or_skip()
    resp = client.get("/api/screener", params={"strategy": "trend_following", "refresh": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["strategy"] == "trend_following"
    assert data["type"] == "technical"
    assert data["passed"] == len(data["candidates"])
    assert data["evaluated"] <= data["universe"]
    for cand in data["candidates"]:
        assert cand["matched_criteria"]  # kandidat lolos pasti punya alasan
        assert {"ticker", "close", "value", "matched_criteria"} <= set(cand)


def test_api_screener_unknown_strategy_404() -> None:
    client = _client_or_skip()
    resp = client.get("/api/screener", params={"strategy": "does_not_exist"})
    assert resp.status_code == 404


def test_api_screener_phase2_unchanged() -> None:
    # Tanpa param strategy: tetap mengembalikan bentuk Phase 2 (bsjp & bpjs).
    client = _client_or_skip()
    resp = client.get("/api/screener", params={"limit": 5, "use_ml": False, "refresh": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "bsjp" in data and "bpjs" in data
    assert isinstance(data["bsjp"], list)
