"""Koneksi database PostgreSQL (SQLAlchemy).

Engine dibuat dari DATABASE_URL di .env. Jika belum diset, engine = None
dan get_db() akan memberi pesan error yang jelas (agar Day 1 tetap bisa
jalan tanpa DB).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class untuk semua ORM models."""


def _normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    # Supabase/Heroku kadang memberi skema "postgres://"; SQLAlchemy 2.x
    # butuh "postgresql://".
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_url(settings.database_url)

engine = None
SessionLocal: sessionmaker[Session] | None = None

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,   # cek koneksi sebelum dipakai (DB cloud sering memutus idle)
        pool_recycle=300,     # daur ulang koneksi tiap 5 menit
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: satu sesi DB per request."""
    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL belum diset di backend/.env. "
            "Isi dengan connection string PostgreSQL (Supabase/Neon)."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
