"""Phase 5 Day 14 — Scheduler malam (job AI).

Struktur jadwal (4 job AI di waktu benar, setelah job quant) + perilaku skip saat
AI nonaktif (tanpa LLM/DB) + eksekusi live ringan (wiring job -> endpoint).
"""

from __future__ import annotations

import pytest

from app.ai import llm_client
from app.scheduler import jobs, scheduler as sched


def _schedule_map():
    return {job_id: (hour, minute) for job_id, _f, hour, minute, _dow in sched.SCHEDULE}


# --------------------------------------------------------------------------- #
# Struktur jadwal (tanpa LLM/DB)
# --------------------------------------------------------------------------- #
def test_ai_jobs_scheduled_at_correct_times():
    times = _schedule_map()
    assert times["knowledge_base_2030"] == (20, 30)
    assert times["ai_analysis_2100"] == (21, 0)
    assert times["market_narrative_2130"] == (21, 30)
    assert times["daily_report_2200"] == (22, 0)


def test_ai_jobs_after_quant_jobs():
    ids = [job_id for job_id, *_ in sched.SCHEDULE]
    # Job AI harus setelah job quant malam (Monte Carlo 20:00).
    assert ids.index("ai_analysis_2100") > ids.index("monte_carlo_2000")
    assert ids.index("daily_report_2200") > ids.index("ai_analysis_2100")


def test_build_scheduler_registers_all_jobs():
    # build_scheduler tidak men-start scheduler (tak perlu shutdown).
    scheduler = sched.build_scheduler()
    assert len(scheduler.get_jobs()) == len(sched.SCHEDULE)


# --------------------------------------------------------------------------- #
# Skip saat AI nonaktif (monkeypatch -> tanpa LLM/DB)
# --------------------------------------------------------------------------- #
def test_ai_jobs_skip_when_ai_off(monkeypatch):
    monkeypatch.setattr(llm_client, "is_available", lambda: False)
    assert jobs.job_refresh_knowledge_base() == 0
    assert jobs.job_generate_ai_analysis() == 0
    assert jobs.job_generate_market_narrative() == 0
    assert jobs.job_generate_daily_report() == 0


# --------------------------------------------------------------------------- #
# Eksekusi live ringan (gated DB+AI)
# --------------------------------------------------------------------------- #
def _skip_unless_ready():
    from app.db.session import SessionLocal

    if SessionLocal is None or not llm_client.is_available():
        pytest.skip("DB/AI belum siap.")


def test_job_ai_analysis_top1_live():
    _skip_unless_ready()
    from sqlalchemy.exc import OperationalError

    try:
        n = jobs.job_generate_ai_analysis(limit=1)
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert isinstance(n, int) and n >= 0


def test_job_market_narrative_live():
    _skip_unless_ready()
    from sqlalchemy import select, func
    from sqlalchemy.exc import OperationalError
    from app.db.session import SessionLocal
    from app.db.models import MarketNarrative

    try:
        r = jobs.job_generate_market_narrative()
    except OperationalError:
        pytest.skip("DB tak terjangkau.")
    assert r == 1
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(MarketNarrative)) >= 1
