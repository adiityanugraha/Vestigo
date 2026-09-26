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


def harian() -> int:
    from app.scheduler import jobs

    log.info("=== mulai job harian TSFM ===")
    n_bar = jobs.job_update_market_data()
    log.info("market data: %s bar", n_bar)
    n_pred = jobs.job_generate_tsfm_predictions()
    n_out = jobs.job_resolve_tsfm_outcomes()
    log.info("=== selesai: %s prediksi, %s outcome ===", n_pred, n_out)
    return 0


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
    a = ap.parse_args()
    _atur_log()
    try:
        return susulan(*a.susulan) if a.susulan else harian()
    except Exception:                                  # noqa: BLE001 - dicatat, bukan ditelan
        log.exception("job harian TSFM GAGAL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
