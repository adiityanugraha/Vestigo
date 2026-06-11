"""SQLAlchemy ORM models — skema database Pocket Screener (Phase 2).

Tabel (sesuai blueprint):
  - stocks            : master daftar saham IDX
  - market_data       : OHLCV harian + indikator teknikal pre-computed
  - screening_history : hasil screener harian (BSJP/BPJS)
  - backtesting       : ringkasan performa strategi
  - user_watchlist    : watchlist per user
  - market_breadth    : ringkasan breadth pasar harian (Day 11)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Stock(Base):
    __tablename__ = "stocks"

    # Ticker dasar IDX tanpa sufiks .JK (mis. "BBCA"). Saat fetch ke Yahoo,
    # backend menambahkan ".JK".
    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128))
    sector: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    market_data: Mapped[list["MarketData"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )


class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_market_data_ticker_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)

    # OHLCV + value (turnover = close * volume)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    value: Mapped[float | None] = mapped_column(Float)

    # Indikator teknikal pre-computed (diisi Day 3).
    # "bb" pada blueprint dipecah jadi 3 band agar bermakna.
    rsi: Mapped[float | None] = mapped_column(Float)
    macd: Mapped[float | None] = mapped_column(Float)
    macd_signal: Mapped[float | None] = mapped_column(Float)
    macd_histogram: Mapped[float | None] = mapped_column(Float)
    bb_upper: Mapped[float | None] = mapped_column(Float)
    bb_middle: Mapped[float | None] = mapped_column(Float)
    bb_lower: Mapped[float | None] = mapped_column(Float)
    atr: Mapped[float | None] = mapped_column(Float)
    vwap: Mapped[float | None] = mapped_column(Float)

    stock: Mapped["Stock"] = relationship(back_populates="market_data")


class ScreeningHistory(Base):
    __tablename__ = "screening_history"
    __table_args__ = (
        UniqueConstraint(
            "date", "ticker", "strategy", name="uq_screening_date_ticker_strategy"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    score: Mapped[float | None] = mapped_column(Float)
    strategy: Mapped[str] = mapped_column(String(8), index=True)  # BSJP | BPJS
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Backtesting(Base):
    __tablename__ = "backtesting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy: Mapped[str] = mapped_column(String(8), index=True)  # BSJP | BPJS
    winrate: Mapped[float | None] = mapped_column(Float)
    cumulative_return: Mapped[float | None] = mapped_column(Float)
    max_drawdown: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MarketBreadth(Base):
    """Ringkasan breadth pasar per tanggal (satu baris per hari bursa).

    Scalar (advancers/decliners/ratio) untuk query cepat; bagian berdaftar
    (top gainers/losers, performa sektor) disimpan sebagai JSONB.
    """

    __tablename__ = "market_breadth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    advancers: Mapped[int] = mapped_column(Integer, default=0)
    decliners: Mapped[int] = mapped_column(Integer, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    bullish_ratio: Mapped[float | None] = mapped_column(Float)  # adv / (adv + dec)

    top_gainers: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    top_losers: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    sector_performance: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserWatchlist(Base):
    __tablename__ = "user_watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Fundamental(Base):
    """Data laporan keuangan per periode (Phase 3 Day 4).

    Satu baris per (ticker, period, report_type). report_type:
      - ANNUAL : laporan tahunan historis (revenue & net_income andal dari Yahoo
                 incomeStatementHistory; dipakai growth YoY / 3-tahun di Day 5).
      - TTM    : snapshot trailing-twelve-month (agregat neraca/profitabilitas:
                 gross_profit, cash, total_debt, roe, eps, dps, common_equity).
      - QUARTER: cadangan bila sumber kuartalan ditambah kemudian.

    Field yang tidak tersedia gratis dari Yahoo untuk IDX dibiarkan None
    (income_from_operations & gross_profit per-tahun, dividend_streak) — lihat
    catatan keterbatasan di data/fundamentals_fetch.py. Berubah lambat
    (kuartalan); refresh harga-sensitif ada di FundamentalDerived.
    """

    __tablename__ = "fundamentals"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "period", "report_type", name="uq_fundamentals_ticker_period_type"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    period: Mapped[str] = mapped_column(String(16), index=True)  # "2025" | "TTM"
    report_type: Mapped[str] = mapped_column(String(8), index=True)  # ANNUAL|TTM|QUARTER

    revenue: Mapped[float | None] = mapped_column(Float)
    net_income: Mapped[float | None] = mapped_column(Float)
    income_from_operations: Mapped[float | None] = mapped_column(Float)
    gross_profit: Mapped[float | None] = mapped_column(Float)
    common_equity: Mapped[float | None] = mapped_column(Float)
    cash_equivalents: Mapped[float | None] = mapped_column(Float)
    total_debt: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Float)
    dps: Mapped[float | None] = mapped_column(Float)
    dividend_streak: Mapped[int | None] = mapped_column(Integer)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StrategyResultRow(Base):
    """Hasil evaluasi SEMUA strategi per saham per hari (Phase 3 Day 7).

    Diisi GET /api/screener/all (lalu scheduler 07:30, Day 13). Satu baris per
    (date, ticker, strategy) — termasuk yang GAGAL (passed=False) karena
    Strategy Matrix (Day 8) butuh pass/fail lengkap. Saham yang tidak bisa
    dievaluasi (data kurang) TIDAK disimpan. matched_criteria & skipped_criteria
    JSONB untuk Explainable AI (Day 10).
    """

    __tablename__ = "strategy_results"
    __table_args__ = (
        UniqueConstraint(
            "date", "ticker", "strategy", name="uq_strategy_results_date_ticker_strategy"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    strategy: Mapped[str] = mapped_column(String(24), index=True)
    passed: Mapped[bool] = mapped_column(Boolean, index=True)
    matched_criteria: Mapped[list[str]] = mapped_column(JSONB, default=list)
    skipped_criteria: Mapped[list[str]] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Forecast(Base):
    """Probability Forecast multi-horizon (Phase 3 Day 12).

    P(return > 0) untuk horizon 1D / 5D / 20D + confidence level (LOW/MEDIUM/
    HIGH). Satu baris per (date, ticker). Diisi GET /api/forecast/{ticker}
    (lalu scheduler 16:15, Day 13).
    """

    __tablename__ = "forecast"
    __table_args__ = (
        UniqueConstraint("date", "ticker", name="uq_forecast_date_ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    prob_1d: Mapped[float | None] = mapped_column(Float)
    prob_5d: Mapped[float | None] = mapped_column(Float)
    prob_20d: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String(8))  # LOW | MEDIUM | HIGH

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StrengthScore(Base):
    """Screener Strength Score lintas-strategi (Phase 3 Day 9).

    Menggabungkan SEMUA strategi yang lolos untuk satu saham menjadi satu skor
    0-100 (berbobot per tipe). Satu baris per (date, ticker). passed_strategies
    JSONB menyimpan daftar key strategi yang lolos pada tanggal itu.
    """

    __tablename__ = "strength_score"
    __table_args__ = (
        UniqueConstraint("date", "ticker", name="uq_strength_date_ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    passed_strategies: Mapped[list[str]] = mapped_column(JSONB, default=list)
    strength: Mapped[int] = mapped_column(Integer, index=True)  # 0-100

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FundamentalDerived(Base):
    """Metrik fundamental yang BERGANTUNG HARGA — refresh harian (Day 5).

    Dipisah dari Fundamental karena PE/PBV/MarketCap/DividendYield berubah tiap
    hari mengikuti harga, sedangkan laporan keuangan murni hanya berubah per
    kuartal. Satu baris per (ticker, date).
    """

    __tablename__ = "fundamental_derived"
    __table_args__ = (
        UniqueConstraint(
            "ticker", "date", name="uq_fundamental_derived_ticker_date"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("stocks.ticker", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)

    pe_annualised: Mapped[float | None] = mapped_column(Float)
    pbv: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    dividend_yield: Mapped[float | None] = mapped_column(Float)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
