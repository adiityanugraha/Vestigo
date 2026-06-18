"""Portfolio AI Advisor (Phase 5 Day 11).

ALOKASI dihitung oleh Portfolio Builder (Phase 4, app.quant.portfolio_builder);
Phase 5 menambahkan lapisan PENJELASAN LLM ("kenapa bobot ini, kenapa saham
ini") sesuai profil risiko. Bobot & angka dari sistem; LLM hanya menjelaskan.

Disclaimer WAJIB: ini alat bantu analisis/edukasi, BUKAN nasihat keuangan.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ai import guardrails, llm_client, prompt_builder
from app.quant import portfolio_builder as pb

_UNIVERSES = ("all", "lq45", "screened")


def _explain(profile: str, result: dict) -> str:
    allocations = result.get("allocations", [])
    tickers = ", ".join(f"{a['ticker']} {round(a['weight'] * 100)}%" for a in allocations)
    template = (
        f"Portofolio profil {profile} terdiri dari {result.get('n_positions')} posisi: {tickers}."
    )
    if not llm_client.is_available():
        return guardrails.ensure_disclaimer(template)
    built = prompt_builder.build(
        (
            f"Jelaskan untuk investor ritel mengapa alokasi portofolio ini cocok untuk profil "
            f"risiko {profile}: 2-3 kalimat ringkasan + alasan SINGKAT tiap bobot saham "
            "(kualitas/skor, risiko, diversifikasi). Gunakan ANGKA dari DATA SISTEM, jangan "
            "mengarang. Tegaskan ini bukan nasihat keuangan."
        ),
        tool_results={
            "risk_profile": profile,
            "allocations": result.get("allocations", []),
            "summary": result.get("summary", {}),
        },
    )
    try:
        text = llm_client.generate(built["prompt"], system=built["system"], max_output_tokens=700)
    except llm_client.LLMError:
        text = template
    return guardrails.ensure_disclaimer(text)


def advise(risk: str, capital: float, universe: str, db: Session) -> dict[str, Any]:
    """Bangun alokasi (Phase 4) + penjelasan LLM. ValueError bila input/hasil invalid."""
    profile = risk.strip().upper()
    if profile not in pb.RISK_PROFILES:
        raise ValueError(f"risk harus salah satu dari {', '.join(pb.RISK_PROFILES)}.")
    universe = universe.strip().lower()
    if universe not in _UNIVERSES:
        raise ValueError("universe harus all|lq45|screened.")

    result = pb.build_portfolio(db, risk_profile=profile, capital=capital, universe=universe)
    if result.get("n_positions", 0) == 0:
        raise ValueError("Tidak ada kandidat yang lolos filter risiko/korelasi untuk profil ini.")

    return {
        "risk_profile": result["risk_profile"],
        "capital": result["capital"],
        "universe": result["universe"],
        "n_positions": result["n_positions"],
        "allocations": result["allocations"],
        "summary": result["summary"],
        "explanation": _explain(profile, result),
        "disclaimer": guardrails.DISCLAIMER,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
