"""SQLAlchemy ORM models — skema database Pocket Screener (Phase 2).

Tabel (sesuai blueprint):
  - stocks            : master daftar saham IDX
  - market_data       : OHLCV harian + indikator teknikal pre-computed
  - screening_history : hasil screener harian (BSJP/BPJS)
  - backtesting       : ringkasan performa strategi
  - user_watchlist    : watchlist per user
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
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
