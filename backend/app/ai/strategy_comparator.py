"""AI Strategy Comparator (Phase 5 Day 10).

Membandingkan DUA strategi memakai metrik dari Strategy Benchmark/Performance
(Phase 4, tabel strategy_performance), lalu LLM menarasikan tradeoff
(return vs drawdown, Sharpe, winrate). ANGKA dari sistem; LLM hanya menarasikan.

PENTING: hanya 5 strategi TEKNIKAL tervalidasi historis (pm.VALIDATED_STRATEGIES)
yang punya metrik. Strategi fundamental DIKECUALIKAN (tak ada data point-in-time)
-> compare() menolak (ValueError) agar LLM tak mengarang metrik yang tak ada.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ai import guardrails, llm_client, prompt_builder
from app.api import performance as performance_api
from app.quant import performance_metrics as pm


def _validate(a: str, b: str) -> tuple[str, str]:
    a, b = a.strip().lower(), b.strip().lower()
    valid = pm.VALIDATED_STRATEGIES
    if a not in valid or b not in valid:
        raise ValueError(
            "Hanya strategi teknikal tervalidasi yang dapat dibandingkan: "
            f"{', '.join(sorted(valid))}. (Strategi fundamental tidak punya metrik "
            "historis sehingga tidak dibandingkan.)"
        )
    if a == b:
        raise ValueError("Pilih dua strategi yang berbeda.")
    return a, b


def _narrate(a: str, b: str, perf_a: dict, perf_b: dict) -> str:
    template = (
        f"Perbandingan {perf_a.get('name', a)} vs {perf_b.get('name', b)} berdasarkan "
        "metrik historis sistem (CAGR, Sharpe, Max Drawdown, Winrate)."
    )
    if not llm_client.is_available():
        return guardrails.ensure_disclaimer(template)
    built = prompt_builder.build(
        (
            f"Bandingkan dua strategi screening, '{a}' dan '{b}', dan jelaskan tradeoff-nya "
            "dalam 3-4 kalimat (mis. return/CAGR vs risiko/Max Drawdown, Sharpe, Winrate). "
            "Gunakan HANYA angka dari DATA SISTEM; jangan mengarang."
        ),
        tool_results={a: perf_a.get("metrics", {}), b: perf_b.get("metrics", {})},
    )
    try:
        text = llm_client.generate(built["prompt"], system=built["system"], max_output_tokens=500)
    except llm_client.LLMError:
        text = template
    return guardrails.ensure_disclaimer(text)


def compare(a: str, b: str, db: Session) -> dict[str, Any]:
    """Bandingkan dua strategi teknikal tervalidasi. ValueError bila pasangan invalid."""
    a, b = _validate(a, b)
    perf_a = performance_api.get_performance(strategy=a, hold=pm.DEFAULT_HOLD, refresh=False, db=db)
    perf_b = performance_api.get_performance(strategy=b, hold=pm.DEFAULT_HOLD, refresh=False, db=db)
    return {
        "strategy_a": a,
        "strategy_b": b,
        "name_a": perf_a.get("name"),
        "name_b": perf_b.get("name"),
        "metrics_a": perf_a.get("metrics", {}),
        "metrics_b": perf_b.get("metrics", {}),
        "comparison": _narrate(a, b, perf_a, perf_b),
        "disclaimer": guardrails.DISCLAIMER,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
