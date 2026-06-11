"""Scheduler APScheduler — jadwal job harian zona waktu WIB (IDX).

Jadwal (Asia/Jakarta) — Phase 2 + tambahan Phase 3 (Day 13):
  07:00  Update market data            -> job_update_market_data
  07:15  Refresh fundamental_derived   -> job_refresh_fundamental_derived   (P3)
  07:30  Jalankan 9 strategi           -> job_run_all_strategies            (P3)
  09:30  Generate screener (BPJS)      -> job_run_screener
  10:00  Generate screener (BPJS)      -> job_run_screener
  15:30  Generate screener (BSJP)      -> job_run_screener
  16:00  Generate ranking              -> job_generate_ranking
  16:15  Probability Forecast          -> job_generate_forecasts            (P3)
  16:30  Strength Score lintas-strategi-> job_generate_strength             (P3)
  17:00  Generate AI report            -> job_generate_reports
  Sabtu 06:00  Update fundamentals     -> job_update_fundamentals           (P3)

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

# (job_id, fungsi, jam, menit, day_of_week) — day_of_week None = setiap hari.
SCHEDULE: list[tuple[str, object, int, int, str | None]] = [
    ("update_market_data", jobs.job_update_market_data, 7, 0, None),
    ("refresh_fundamental_derived", jobs.job_refresh_fundamental_derived, 7, 15, None),
    ("run_all_strategies", jobs.job_run_all_strategies, 7, 30, None),
    ("screener_bpjs_0930", jobs.job_run_screener, 9, 30, None),
    ("screener_bpjs_1000", jobs.job_run_screener, 10, 0, None),
    ("screener_bsjp_1530", jobs.job_run_screener, 15, 30, None),
    ("ranking_1600", jobs.job_generate_ranking, 16, 0, None),
    ("forecast_1615", jobs.job_generate_forecasts, 16, 15, None),
    ("strength_1630", jobs.job_generate_strength, 16, 30, None),
    ("ai_report_1700", jobs.job_generate_reports, 17, 0, None),
    # Mingguan: data fundamental berubah per kuartal (Sabtu pagi, pasar tutup).
    ("update_fundamentals_weekly", jobs.job_update_fundamentals, 6, 0, "sat"),
]

_scheduler: BackgroundScheduler | None = None


def build_scheduler() -> BackgroundScheduler:
    """Buat scheduler terkonfigurasi (BELUM start) dengan seluruh job terdaftar."""
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    for job_id, func, hour, minute, day_of_week in SCHEDULE:
        scheduler.add_job(
            func,
            trigger=CronTrigger(
                hour=hour, minute=minute, day_of_week=day_of_week, timezone=TIMEZONE
            ),
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
