"""Inisialisasi database: create tables + seed daftar saham.

Jalankan (dari folder backend/, venv aktif, DATABASE_URL terisi di .env):
    python -m app.db.init_db

Idempotent: aman dijalankan berulang. create_all hanya membuat tabel yang
belum ada; seed memakai upsert (merge) sehingga tidak menduplikasi.
"""

from __future__ import annotations

# Import semua model agar terdaftar di Base.metadata sebelum create_all.
from app.db import models  # noqa: F401
from app.db.models import Stock
from app.db.seed_data import IDX_STOCKS
from app.db.session import Base, SessionLocal, engine


def create_tables() -> None:
    if engine is None:
        raise RuntimeError(
            "DATABASE_URL belum diset di backend/.env. "
            "Isi connection string PostgreSQL lebih dulu."
        )
    Base.metadata.create_all(bind=engine)


def seed_stocks() -> int:
    """Upsert seluruh IDX_STOCKS; kembalikan total baris di tabel stocks."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL belum diset di backend/.env.")
    with SessionLocal() as db:
        for ticker, name, sector in IDX_STOCKS:
            db.merge(Stock(ticker=ticker, name=name, sector=sector))
        db.commit()
        return db.query(Stock).count()


def main() -> None:
    print("Membuat tabel...")
    create_tables()
    print("  OK: tabel dibuat / sudah ada.")

    print(f"Seeding {len(IDX_STOCKS)} saham IDX ke tabel stocks...")
    total = seed_stocks()
    print(f"  OK: tabel stocks berisi {total} saham.")
    print("Selesai.")


if __name__ == "__main__":
    main()
