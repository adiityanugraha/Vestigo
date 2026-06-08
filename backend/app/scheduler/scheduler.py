"""Scheduler APScheduler (Day 13) — jadwal job harian zona waktu WIB (IDX).

Jadwal (Asia/Jakarta), sesuai Step_by_Step Phase 2:
  07:00  Update market data        -> job_update_market_data
  09:30  Generate screener (BPJS)  -> job_run_screener
  10:00  Generate screener (BPJS)  -> job_run_screener
  15:30  Generate screener (BSJP)  -> job_run_screener
  16:00  Generate ranking          -> job_generate_ranking
  17:00  Generate AI report        -> job_generate_reports

Catatan: job_run_screener menghitung KEDUA strategi (BSJP & BPJS) sekaligus; jam
yang berbeda mewakili fase sesi bursa (pagi/sore) saat hasil di-refresh.

Pakai BackgroundScheduler (thread terpisah) karena job memakai sesi DB sinkron,
agar tidak memblokir event loop FastAPI. Diintegrasikan ke startup via lifespan.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.scheduler import jobs

log = logging.getLogger("scheduler")

TIMEZONE = "Asia/Jakarta"

# (job_id, fungsi, jam, menit)
SCHEDULE: list[tuple[str, object, int, int]] = [
    ("update_market_data", jobs.job_update_market_data, 7, 0),
    ("screener_bpjs_0930", jobs.job_run_screener, 9, 30),
    ("screener_bpjs_1000", jobs.job_run_screener, 10, 0),
    ("screener_bsjp_1530", jobs.job_run_screener, 15, 30),
    ("ranking_1600", jobs.job_generate_ranking, 16, 0),
    ("ai_report_1700", jobs.job_generate_reports, 17, 0),
]

_scheduler: BackgroundScheduler | None = None


def build_scheduler() -> BackgroundScheduler:
    """Buat scheduler terkonfigurasi (BELUM start) dengan seluruh job terdaftar."""
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    for job_id, func, hour, minute in SCHEDULE:
        scheduler.add_job(
            func,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=TIMEZONE),
            id=job_id,
            name=job_id,
            replace_existing=True,
            coalesce=True,  # gabung eksekusi yang menumpuk jadi satu
            max_instances=1,  # cegah job sama jalan tumpang tindih
            misfire_grace_time=3600,  # toleransi telat eksekusi 1 jam
        )
    return scheduler


def start() -> BackgroundScheduler:
    """Bangun & jalankan scheduler (idempoten — start kedua diabaikan)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler
    _scheduler = build_scheduler()
    _scheduler.start()
    log.info("Scheduler aktif (%s) dengan %s job.", TIMEZONE, len(SCHEDULE))
    return _scheduler


def shutdown() -> None:
    """Hentikan scheduler bila berjalan."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("Scheduler dihentikan.")
    _scheduler = None
