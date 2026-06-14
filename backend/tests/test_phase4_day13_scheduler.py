"""Phase 4 Day 13 — Scheduler job malam quant.

Struktur jadwal diuji murni; eksekusi job diuji dgn DB (auto-skip bila tak ada).
"""

from __future__ import annotations

import pytest

from app.scheduler import jobs, scheduler

PHASE4_IDS = {
    "quant_metrics_1800",
    "correlation_1900",
    "monte_carlo_2000",
    "replay_returns_weekly",
    "walk_forward_weekly",
}


def test_schedule_has_phase4_jobs() -> None:
    ids = {entry[0] for entry in scheduler.SCHEDULE}
    assert PHASE4_IDS <= ids


def test_schedule_times_correct() -> None:
    by_id = {e[0]: e for e in scheduler.SCHEDULE}
    assert by_id["quant_metrics_1800"][2:5] == (18, 0, None)
    assert by_id["correlation_1900"][2:5] == (19, 0, None)
    assert by_id["monte_carlo_2000"][2:5] == (20, 0, None)
    # Job berkala berjalan Sabtu.
    assert by_id["replay_returns_weekly"][4] == "sat"
    assert by_id["walk_forward_weekly"][4] == "sat"


def test_quant_metrics_run_after_market_close() -> None:
    by_id = {e[0]: e for e in scheduler.SCHEDULE}

    def minute_of_day(entry):
        return entry[2] * 60 + entry[3]

    # Metrik malam (18:00) setelah ranking (16:00) & report (17:00).
    assert minute_of_day(by_id["quant_metrics_1800"]) > minute_of_day(by_id["ai_report_1700"])
    # MC (20:00) setelah correlation (19:00) setelah metrics (18:00).
    assert (
        minute_of_day(by_id["quant_metrics_1800"])
        < minute_of_day(by_id["correlation_1900"])
        < minute_of_day(by_id["monte_carlo_2000"])
    )


def test_build_scheduler_registers_phase4_jobs() -> None:
    sched = scheduler.build_scheduler()
    try:
        registered = {job.id for job in sched.get_jobs()}
        assert registered == {entry[0] for entry in scheduler.SCHEDULE}
        assert PHASE4_IDS <= registered
    finally:
        if sched.running:
            sched.shutdown(wait=False)


# --------------------------------------------------------------------------- #
# Eksekusi job (butuh DB)
# --------------------------------------------------------------------------- #
def _require_db():
    from app.db.session import SessionLocal

    if SessionLocal is None:
        pytest.skip("DATABASE_URL tidak diset — lewati test eksekusi job.")


def test_job_refresh_replay_returns_subset() -> None:
    _require_db()
    persisted = jobs.job_refresh_replay_returns(tickers=["BBCA"])
    assert persisted > 0


def test_job_update_correlation() -> None:
    _require_db()
    n = jobs.job_update_correlation(universe="lq45")
    assert n >= 2


def test_job_generate_quant_metrics() -> None:
    _require_db()
    n = jobs.job_generate_quant_metrics()
    assert n == 5  # 5 strategi tervalidasi → 5 equity curve


def test_job_run_monte_carlo() -> None:
    _require_db()
    warmed = jobs.job_run_monte_carlo()
    assert warmed == 5


def test_job_refresh_walk_forward() -> None:
    _require_db()
    warmed = jobs.job_refresh_walk_forward()
    assert warmed == 5
