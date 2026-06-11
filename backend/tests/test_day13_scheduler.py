"""Day 13 — Scheduler Phase 3: jadwal job baru + eksekusi job.

Struktur jadwal diuji murni (tanpa DB). Eksekusi job baru diuji dgn DB + model
sungguhan atas subset kecil ticker (auto-skip bila tak ada DB).
"""

from __future__ import annotations

import pytest

from app.scheduler import jobs, scheduler


# --------------------------------------------------------------------------- #
# Struktur jadwal (murni)
# --------------------------------------------------------------------------- #
def test_schedule_has_phase3_jobs() -> None:
    ids = {entry[0] for entry in scheduler.SCHEDULE}
    assert {
        "refresh_fundamental_derived",
        "run_all_strategies",
        "forecast_1615",
        "strength_1630",
        "update_fundamentals_weekly",
    } <= ids


def test_schedule_times_correct() -> None:
    by_id = {e[0]: e for e in scheduler.SCHEDULE}
    # (id, func, hour, minute, day_of_week)
    assert by_id["refresh_fundamental_derived"][2:5] == (7, 15, None)
    assert by_id["run_all_strategies"][2:5] == (7, 30, None)
    assert by_id["forecast_1615"][2:5] == (16, 15, None)
    assert by_id["strength_1630"][2:5] == (16, 30, None)
    # job mingguan berjalan Sabtu
    assert by_id["update_fundamentals_weekly"][4] == "sat"


def test_build_scheduler_registers_all_jobs() -> None:
    sched = scheduler.build_scheduler()
    try:
        registered = {job.id for job in sched.get_jobs()}
        assert registered == {entry[0] for entry in scheduler.SCHEDULE}
        # CronTrigger weekly punya day_of_week, harian tidak membatasi hari.
    finally:
        if sched.running:
            sched.shutdown(wait=False)


def test_ordering_strategies_before_strength() -> None:
    # Strength (16:30) harus SETELAH run_all_strategies (07:30) karena membaca
    # strategy_results. Sanity urutan menit-dalam-hari.
    by_id = {e[0]: e for e in scheduler.SCHEDULE}

    def minute_of_day(entry):
        return entry[2] * 60 + entry[3]

    assert minute_of_day(by_id["run_all_strategies"]) < minute_of_day(by_id["strength_1630"])
    assert minute_of_day(by_id["refresh_fundamental_derived"]) < minute_of_day(
        by_id["run_all_strategies"]
    )


# --------------------------------------------------------------------------- #
# Eksekusi job (butuh DB; subset kecil agar cepat)
# --------------------------------------------------------------------------- #
def _require_db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test eksekusi job.")


def test_job_run_all_strategies() -> None:
    _require_db()
    persisted = jobs.job_run_all_strategies()
    assert persisted > 0  # 80 saham x 9 strategi (yang dievaluasi)


def test_job_refresh_fundamental_derived() -> None:
    _require_db()
    ok = jobs.job_refresh_fundamental_derived()
    assert ok > 0


def test_job_generate_forecasts_subset() -> None:
    _require_db()
    from pathlib import Path

    from app.ml import forecast_model

    ml_dir = Path(forecast_model.__file__).resolve().parent
    if not (ml_dir / "forecast_1d.onnx").exists():
        pytest.skip("Model forecast belum dilatih.")
    generated = jobs.job_generate_forecasts(tickers=["BBCA", "ASII"])
    assert generated == 2


def test_job_generate_strength_subset() -> None:
    _require_db()
    # Pastikan strategy_results ada lebih dulu.
    jobs.job_run_all_strategies()
    generated = jobs.job_generate_strength(tickers=["BBCA", "ASII"])
    assert generated >= 1
