"""Job harian Vestigo-TSFM tanpa backend yang menyala terus (Phase 6, M8/M10).

Dipanggil Windows Task Scheduler sekali sehari. Pengganti scheduler APScheduler
untuk laptop: APScheduler hanya tahu jadwal selama proses backend hidup, jadi
kalau laptop mati jam 07:45, job hari itu hilang begitu saja. Task Scheduler
dengan opsi "run as soon as possible after a scheduled start is missed" justru
menjalankannya begitu laptop menyala.

Urutan (sama dengan jadwal backend 07:00 -> 07:45 -> 07:50):
  1. update market data   - menimpa bar setengah jadi dengan versi final
  2. prediksi TSFM        - sesi final terakhir; ditandai susulan bila telat
  3. realisasi outcome    - prediksi yang horizon 10 sesinya sudah lewat

Mode susulan, untuk hari bursa yang terlewat penuh:
    python -m app.scheduler.tsfm_harian --susulan 2026-09-28 2026-10-02
Prediksinya identik dengan versi live (model dan bar final tidak berubah), tapi
selalu ditandai susulan dan tidak masuk track record live. Hari yang sudah punya
prediksi dilewati, jadi versi live tidak pernah tertimpa.

Log: backend/logs/tsfm_harian.log
"""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pandas as pd

LOG = Path(__file__).resolve().parents[2] / "logs" / "tsfm_harian.log"
log = logging.getLogger("tsfm_harian")

# Dump DB ke disk fisik lain (C, bukan E tempat proyek): prediksi live M10 tidak
# bisa dibuat ulang. Disalin ke flashdisk oleh vestigo-tsfm/scripts/backup.ps1.
BACKUP_DB = Path(r"C:\Backup\Vestigo\db")
PG_DUMP = Path(r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe")
SIMPAN_DUMP = 7         # dump terbaru selalu superset yang lama, 7 hari cukup


def _atur_log() -> None:
    LOG.parent.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    berkas = RotatingFileHandler(LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    berkas.setFormatter(fmt)
    handlers: list[logging.Handler] = [berkas]
    # pythonw (dipakai Task Scheduler agar tidak memunculkan jendela) tidak punya
    # stdout; StreamHandler ke None akan gagal saat menulis.
    if sys.stdout is not None:
        layar = logging.StreamHandler(sys.stdout)
        layar.setFormatter(fmt)
        handlers.append(layar)
    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)      # 81 baris per hari tidak berguna


def _pastikan_db_lokal() -> None:
    """Job ini menulis ke DB sumber (track record M10). Kalau DATABASE_URL tertukar
    dengan URL produksi, prediksi live akan tercecer ke DB yang tiap pagi ditimpa."""
    from sqlalchemy.engine import make_url

    from app.db.session import DATABASE_URL

    host = make_url(DATABASE_URL).host if DATABASE_URL else None
    if host not in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError(f"DATABASE_URL harus DB lokal, bukan {host!r}. "
                           "URL produksi (Aiven) tempatnya di PROD_DATABASE_URL.")


def harian() -> int:
    from app.scheduler import jobs

    _pastikan_db_lokal()
    log.info("=== mulai job harian TSFM ===")
    n_bar = jobs.job_update_market_data()
    log.info("market data: %s bar", n_bar)
    n_pred = jobs.job_generate_tsfm_predictions()
    n_out = jobs.job_resolve_tsfm_outcomes()
    log.info("=== selesai: %s prediksi, %s outcome ===", n_pred, n_out)
    try:
        sync_produksi(dump_db())
    except Exception:                                  # noqa: BLE001 - prediksi sudah tersimpan
        log.exception("dump / sync DB GAGAL")
    return 0


def _libpq_env(url: str) -> tuple[list[str], dict[str, str]]:
    """Argumen koneksi + env untuk pg_dump/pg_restore. Password lewat env, bukan
    argumen, supaya tidak terlihat di daftar proses."""
    import os

    from sqlalchemy.engine import make_url

    u = make_url(url)
    env = {**os.environ, "PGPASSWORD": u.password or ""}
    if "sslmode" in u.query:                           # Aiven: ?sslmode=require
        env["PGSSLMODE"] = str(u.query["sslmode"])
    return ["-h", u.host or "localhost", "-p", str(u.port or 5432), "-U", u.username,
            "-d", u.database], env


def _jalankan(args: list[str], env: dict[str, str]) -> None:
    import subprocess

    r = subprocess.run(args, env=env, capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode:
        raise RuntimeError(f"{Path(args[0]).name} gagal ({r.returncode}): {r.stderr.strip()[-2000:]}")


def dump_db() -> Path:
    from datetime import date

    from app.db.session import DATABASE_URL

    BACKUP_DB.mkdir(parents=True, exist_ok=True)
    tujuan = BACKUP_DB / f"vestigo_{date.today():%Y-%m-%d}.dump"
    sementara = tujuan.with_suffix(".tmp")
    koneksi, env = _libpq_env(DATABASE_URL)
    try:
        _jalankan([str(PG_DUMP), "-Fc", *koneksi, "-f", str(sementara)], env)
    finally:
        # pg_dump yang gagal meninggalkan file 0 byte; jangan sampai ia menimpa
        # dump sehat hari yang sama atau ikut dihitung rotasi SIMPAN_DUMP.
        if sementara.exists() and sementara.stat().st_size == 0:
            sementara.unlink()
    sementara.replace(tujuan)
    for lama in sorted(BACKUP_DB.glob("vestigo_*.dump"))[:-SIMPAN_DUMP]:
        lama.unlink()
    log.info("dump DB: %s (%.1f MB)", tujuan.name, tujuan.stat().st_size / 1e6)
    return tujuan


def sync_produksi(dump: Path) -> None:
    """Timpa DB produksi dengan dump DB lokal. Satu transaksi: pengunjung melihat
    data lama sampai commit, dan kalau gagal di tengah, produksi tidak berubah.
    ponytail: salin penuh ~90 MB/hari; sinkron per tabel kalau DB membesar."""
    from app.core.config import get_settings

    url = get_settings().prod_database_url
    if not url:
        return
    koneksi, env = _libpq_env(url)
    _jalankan([str(PG_DUMP.with_name("pg_restore.exe")), "--clean", "--if-exists", "--no-owner",
               "--no-privileges", "--single-transaction", *koneksi, str(dump)], env)
    log.info("sync produksi: %s -> %s", dump.name, _libpq_env(url)[0][1])


def susulan(dari: str, sampai: str) -> int:
    from sqlalchemy import select

    from app.db.models import TsfmPrediction
    from app.db.session import SessionLocal
    from app.ml import tsfm_inference as ti
    from app.scheduler import jobs

    with SessionLocal() as db:
        sesi = ti.sesi_final(ti.load_bars(db))
        ada = set(db.scalars(select(TsfmPrediction.prediction_date).distinct()
                             .where(TsfmPrediction.model_version == ti.MODEL_VERSION)))
    target = [s for s in sesi[(sesi >= pd.Timestamp(dari)) & (sesi <= pd.Timestamp(sampai))]
              if s.date() not in ada]
    log.info("susulan %s .. %s: %s sesi tanpa prediksi %s", dari, sampai, len(target),
             [str(s.date()) for s in target])
    for s in target:
        jobs.job_generate_tsfm_predictions(as_of=s, paksa_susulan=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Job harian Vestigo-TSFM")
    ap.add_argument("--susulan", nargs=2, metavar=("DARI", "SAMPAI"),
                    help="hitung prediksi untuk sesi terlewat (YYYY-MM-DD YYYY-MM-DD)")
    ap.add_argument("--sync", action="store_true",
                    help="hanya dump DB lokal lalu salin ke produksi (PROD_DATABASE_URL)")
    a = ap.parse_args()
    _atur_log()
    try:
        if a.sync:
            _pastikan_db_lokal()
            sync_produksi(dump_db())
            return 0
        return susulan(*a.susulan) if a.susulan else harian()
    except Exception:                                  # noqa: BLE001 - dicatat, bukan ditelan
        log.exception("job harian TSFM GAGAL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
