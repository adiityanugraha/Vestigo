"""Phase 6 M8 - integrasi Vestigo-TSFM.

Uji murni (tanpa DB). Uji yang butuh model ONNX 137 MB otomatis dilewati bila
berkasnya belum disalin ke app/ml/tsfm.onnx.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.ml import tsfm_inference as ti
from app.scheduler import scheduler

FIXTURE = Path(__file__).parent / "fixtures" / "tsfm_channels.npz"
ADA_MODEL = ti.model_tersedia()


def _bars(z, tk):
    b = z[f"{tk}_bars"]
    return pd.DataFrame({"date": b[:, 0].astype("int32").astype("datetime64[D]"),
                         "open": b[:, 1], "high": b[:, 2], "low": b[:, 3],
                         "close": b[:, 4], "volume": b[:, 5]})


def test_jadwal_tsfm_setelah_market_data():
    by_id = {e[0]: e for e in scheduler.SCHEDULE}
    menit = lambda e: e[2] * 60 + e[3]
    assert menit(by_id["tsfm_predict_0745"]) > menit(by_id["update_market_data"])
    assert menit(by_id["tsfm_outcomes_0750"]) > menit(by_id["tsfm_predict_0745"])
    assert menit(by_id["tsfm_predict_0745"]) < 9 * 60          # sebelum bursa buka


def test_data_basi_menolak_pipeline_mati():
    sesi = pd.DatetimeIndex(["2026-07-08", "2026-07-09", "2026-07-10"])
    assert ti.data_basi(sesi, hari_ini=date(2026, 7, 13)) is None       # akhir pekan: segar
    assert ti.data_basi(sesi, hari_ini=date(2026, 9, 24)) == 76         # kasus nyata


def test_sesi_final_membuang_hari_ini():
    """Bar bertanggal hari ini bisa setengah jadi - tidak boleh jadi input."""
    d = pd.bdate_range("2026-01-01", periods=30)
    bars = {"A": pd.DataFrame({"date": d, "close": 1.0, "volume": 1.0})}
    sesi = ti.sesi_final(bars, hari_ini=d[-1].date())
    assert d[-1] not in sesi and d[-2] in sesi


def test_realisasi_sama_dengan_definisi_label():
    d = pd.bdate_range("2026-01-01", periods=15)
    c = 100 * np.exp(np.cumsum(np.full(15, 0.01)))
    bars = pd.DataFrame({"date": d, "close": c, "volume": 1e6})
    ret, vol = ti.realisasi(bars, d, d[0], horizon=10)
    assert np.isclose(ret, 0.10) and np.isclose(vol, 0.0, atol=1e-12)
    assert ti.realisasi(bars, d, d[10], horizon=10) is None             # belum lewat 10 sesi
    bars.loc[5, "volume"] = 0                                            # bar tanpa transaksi
    assert ti.realisasi(bars, d, d[0], horizon=10) is None


@pytest.mark.skipif(not (ADA_MODEL and FIXTURE.exists()), reason="model/fixture TSFM tidak ada")
def test_predict_all_dari_fixture():
    z = np.load(FIXTURE)
    tickers = [str(t) for t in z["tickers"]]
    bars = {tk: _bars(z, tk) for tk in tickers}
    sesi = pd.DatetimeIndex(z["BBCA_sessions"].astype("datetime64[D]"))
    as_of, pred = ti.predict_all(bars, sesi)
    assert as_of == sesi[-1]
    assert {p["ticker"] for p in pred} == set(tickers)
    for p in pred:
        assert abs(p["prob_down"] + p["prob_flat"] + p["prob_up"] - 1) < 1e-5
        assert 0 <= p["rank_pct"] <= 1 and p["predicted_vol"] > 0
        assert p["regime"] in ti.REGIME and p["bad_rows"] <= 8
    pct = sorted(p["rank_pct"] for p in pred)
    assert pct[0] == 0 and pct[-1] == 1


def test_model_card_konsisten():
    from app.api.tsfm import model_card

    k = model_card()
    assert k["model_version"] == ti.MODEL_VERSION
    assert "bukan sinyal beli" in k["ringkasan"]
    assert k["paritas_onnx"]["lulus"] and k["paritas_onnx"]["maks_selisih"] < 1e-4
    assert len(k["walk_forward"]["per_fold"]) == k["walk_forward"]["n_fold"] == 10
