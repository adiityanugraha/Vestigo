"""Runner generik: jalankan SATU strategi (dari registry) atas seluruh universe.

Dipakai endpoint GET /api/screener?strategy={name} (Day 3) dan menjadi fondasi
GET /api/screener/all + strategy_results (Day 7). Berbeda dari app.api.screener
(jalur Phase 2 BSJP/BPJS + ML + levels), runner ini netral-strategi: ia hanya
mengembalikan kandidat yang LOLOS beserta matched_criteria (penjelasan otomatis).

Indeks (IHSG) dikecualikan — bukan saham tradable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.instruments import is_index
from app.core.strategies import registry
from app.core.strategies.base import StockData
from app.db.models import MarketData, Stock


def load_bars_by_ticker(db: Session) -> dict[str, list[MarketData]]:
    """Semua bar market_data dikelompokkan per ticker, urut kronologis."""
    rows = db.scalars(select(MarketData).order_by(MarketData.ticker, MarketData.date))
    grouped: dict[str, list[MarketData]] = {}
    for row in rows:
        grouped.setdefault(row.ticker, []).append(row)
    return grouped


def _candidate(ticker: str, bars: list[MarketData], matched: list[str], stock: Stock | None) -> dict:
    latest = bars[-1]
    return {
        "ticker": ticker,
        "name": stock.name if stock else None,
        "sector": stock.sector if stock else None,
        "date": latest.date.isoformat(),
        "open": latest.open,
        "close": latest.close,
        "volume": float(latest.volume) if latest.volume is not None else 0.0,
        "value": latest.value if latest.value is not None else 0.0,
        "matched_criteria": matched,
    }


def screen_one_strategy(db: Session, strategy_key: str, limit: int | None = None) -> dict:
    """Jalankan satu strategi atas seluruh ticker.

    Mengembalikan ringkasan (universe/evaluated/passed) + daftar kandidat lolos,
    diurutkan menurun berdasarkan nilai transaksi (turnover) sebagai proxy
    likuiditas yang berlaku universal untuk strategi teknikal & fundamental.

    KeyError bila strategy_key tidak terdaftar (caller -> HTTP 404).
    """
    strategy = registry.get(strategy_key)
    if strategy is None:
        raise KeyError(strategy_key)

    bars_by_ticker = load_bars_by_ticker(db)
    stock_map = {stock.ticker: stock for stock in db.scalars(select(Stock))}

    candidates: list[dict] = []
    evaluated = 0
    for ticker, bars in bars_by_ticker.items():
        if is_index(ticker):
            continue
        result = strategy.run(StockData(ticker=ticker, bars=bars))
        if not result.evaluated:
            continue
        evaluated += 1
        if result.passed:
            candidates.append(
                _candidate(ticker, bars, result.matched_criteria, stock_map.get(ticker))
            )

    candidates.sort(key=lambda c: c["value"] or 0.0, reverse=True)
    passed_count = len(candidates)  # total lolos, sebelum dipangkas limit
    if limit is not None:
        candidates = candidates[:limit]

    return {
        "strategy": strategy.key,
        "name": strategy.name,
        "type": strategy.type.value,
        "output_label": strategy.output_label,
        "universe": sum(1 for t in bars_by_ticker if not is_index(t)),
        "evaluated": evaluated,
        "passed": passed_count,
        "candidates": candidates,
    }
