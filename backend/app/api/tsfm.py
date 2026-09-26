"""Vestigo-TSFM API (Phase 6, M8).

GET /api/tsfm/predictions   peringkat harian dari model, terbaru atau per tanggal
GET /api/tsfm/track-record  IC live dari prediksi yang sudah terealisasi (M10)
GET /api/tsfm/model-card    hasil riset lengkap, termasuk temuan negatif
GET /api/tsfm/ui/{nama}     data halaman UI (performance, calibration, backtest,
                            training) - dihitung dari artefak riset oleh
                            vestigo-tsfm/scripts/export_ui.py, tidak diketik tangan

Setiap respons membawa `status_riset` - ringkasan jujur apa yang terbukti dan
apa yang tidak. Ini bukan disclaimer formalitas: backtest 2016-2024 menunjukkan
strategi di atas skor ini kalah dari beli-tahan IHSG setelah biaya, dan UI yang
menampilkan peringkat tanpa konteks itu akan menyesatkan.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from scipy.stats import spearmanr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Stock, TsfmOutcome, TsfmPrediction
from app.db.session import get_db
from app.ml.tsfm_inference import MODEL_VERSION

router = APIRouter(prefix="/api/tsfm", tags=["tsfm"])

MODEL_CARD = Path(__file__).resolve().parents[1] / "ml" / "tsfm_model_card.json"
UI_DIR = Path(__file__).resolve().parents[1] / "ml" / "tsfm_ui"
UI_DATA = ("performance", "calibration", "backtest", "training")
MIN_EMITEN_IC = 20            # sama dgn metrik riset: IC per hari butuh cross-section cukup


@lru_cache(maxsize=1)
def model_card() -> dict:
    if not MODEL_CARD.exists():
        raise HTTPException(503, "Model card TSFM belum dibuat (vestigo-tsfm/scripts/make_model_card.py)")
    return json.loads(MODEL_CARD.read_text(encoding="utf-8"))


def _status() -> dict:
    k = model_card()
    return {"ringkasan": k["ringkasan"], "gunakan": k["per_keluaran"]["rank_score"],
            "jangan": k["per_keluaran"]["prob_arah"]}


@router.get("/predictions")
def predictions(tanggal: date | None = Query(None, description="default: tanggal prediksi terbaru"),
                limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)) -> dict:
    if tanggal is None:
        tanggal = db.scalar(select(func.max(TsfmPrediction.prediction_date))
                            .where(TsfmPrediction.model_version == MODEL_VERSION))
        if tanggal is None:
            raise HTTPException(404, "Belum ada prediksi TSFM. Jalankan job_generate_tsfm_predictions.")
    rows = db.execute(
        select(TsfmPrediction, Stock.name, Stock.sector)
        .join(Stock, Stock.ticker == TsfmPrediction.ticker, isouter=True)
        .where(TsfmPrediction.prediction_date == tanggal,
               TsfmPrediction.model_version == MODEL_VERSION)
        .order_by(TsfmPrediction.rank_score.desc()).limit(limit)
    ).all()
    return {
        "prediction_date": tanggal, "model_version": MODEL_VERSION, "horizon_days": 10,
        "n": len(rows), "status_riset": _status(),
        "predictions": [{
            "ticker": r.ticker, "name": nama, "sector": sektor,
            "rank_score": r.rank_score, "rank_pct": r.rank_pct,
            "predicted_vol": r.predicted_vol, "regime": r.regime, "regime_prob": r.regime_prob,
            "prob": {"down": r.prob_down, "flat": r.prob_flat, "up": r.prob_up},
            "bad_rows": r.bad_rows,
        } for r, nama, sektor in rows],
    }


@router.get("/track-record")
def track_record(db: Session = Depends(get_db)) -> dict:
    """IC live: korelasi peringkat skor vs return yang benar-benar terjadi, per hari.

    Dihitung dengan definisi yang sama dengan riset (Spearman per hari, minimal
    20 emiten). Blueprint M10: dilaporkan apa adanya, termasuk kalau negatif.
    """
    semua = db.execute(
        select(TsfmPrediction.prediction_date, TsfmPrediction.rank_score, TsfmOutcome.realized_return,
               TsfmPrediction.susulan)
        .join(TsfmOutcome, TsfmOutcome.prediction_id == TsfmPrediction.id)
        .where(TsfmPrediction.model_version == MODEL_VERSION)
    ).all()
    # Track record live hanya dari prediksi yang dibuat sebelum horizonnya mulai
    # terlihat. Baris susulan dihitung terpisah, tidak dicampur diam-diam.
    rows = [(d, s, r) for d, s, r, sus in semua if not sus]
    n_susulan = sum(1 for *_, sus in semua if sus)
    per_hari: dict = {}
    for d, s, r in rows:
        per_hari.setdefault(d, []).append((s, r))
    harian = []
    for d in sorted(per_hari):
        v = per_hari[d]
        if len(v) >= MIN_EMITEN_IC:
            s, r = zip(*v)
            harian.append({"tanggal": d, "ic": float(spearmanr(s, r).correlation), "n": len(v)})
    ic = np.array([h["ic"] for h in harian])
    ringkas = None
    if len(ic) >= 2:
        ringkas = {"ic_rata": float(ic.mean()), "ic_std": float(ic.std(ddof=1)),
                   "icir": float(ic.mean() / ic.std(ddof=1)) if ic.std(ddof=1) > 0 else None,
                   "ic_positif_pct": float((ic > 0).mean() * 100)}
    riset = model_card()["walk_forward"]
    return {
        "model_version": MODEL_VERSION, "n_prediksi_terealisasi": len(rows),
        "n_susulan_dikecualikan": n_susulan,
        "n_hari": len(harian), "target_m10_hari": 60, "ringkasan": ringkas,
        "pembanding_riset": {"ic_walk_forward": riset["ic_netral_rata"],
                             "catatan": "IC riset dinetralkan terhadap volatilitas; IC live di sini mentah."},
        "harian": harian,
    }


@router.get("/model-card")
def get_model_card() -> dict:
    return model_card()


@lru_cache(maxsize=len(UI_DATA))
def _ui(nama: str) -> dict:
    return json.loads((UI_DIR / f"{nama}.json").read_text(encoding="utf-8"))


@router.get("/ui/{nama}")
def ui_data(nama: str) -> dict:
    if nama not in UI_DATA:
        raise HTTPException(404, f"Data UI tidak dikenal: {nama}")
    if not (UI_DIR / f"{nama}.json").exists():
        raise HTTPException(503, "Data UI TSFM belum diekspor (vestigo-tsfm/scripts/export_ui.py)")
    return _ui(nama)
