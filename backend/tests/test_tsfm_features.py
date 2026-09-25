"""Paritas preprocessing Vestigo-TSFM terhadap training (M8).

Fixture berisi, per emiten, OHLCV mentah + daftar sesi + window 512x5 yang
benar-benar dilihat model saat training. Uji ini memastikan app.ml.tsfm_features
menghasilkan window yang sama dari input yang sama. Kalau gagal, JANGAN longgarkan
toleransinya - model akan menerima input yang tidak pernah ia pelajari.

Regenerasi fixture: python vestigo-tsfm/scripts/make_vestigo_fixture.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.ml.tsfm_features import CONTEXT, build_window

FIXTURE = Path(__file__).parent / "fixtures" / "tsfm_channels.npz"


def _bars(z, tk):
    b = z[f"{tk}_bars"]
    return pd.DataFrame({"date": b[:, 0].astype("int32").astype("datetime64[D]"),
                         "open": b[:, 1], "high": b[:, 2], "low": b[:, 3],
                         "close": b[:, 4], "volume": b[:, 5]})


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture TSFM belum dibuat")
@pytest.mark.parametrize("tk", ["BBCA", "TLKM", "ACES", "ADRO", "MDRN", "ABBA"])
def test_window_identik_dengan_training(tk):
    z = np.load(FIXTURE)
    sessions = pd.DatetimeIndex(z[f"{tk}_sessions"].astype("datetime64[D]"))
    hasil = build_window(_bars(z, tk), sessions)
    assert hasil is not None
    w, buruk = hasil
    acuan = z[f"{tk}_window"].T                       # (5, 512)
    assert w.shape == acuan.shape == (5, CONTEXT)
    selisih = np.abs(w - acuan).max()
    assert selisih < 1e-5, f"{tk}: kanal menyimpang {selisih:.2e} dari training"


def test_window_ditolak_bila_riwayat_kurang():
    d = pd.bdate_range("2026-01-01", periods=100)
    bars = pd.DataFrame({"date": d, "open": 100.0, "high": 101.0, "low": 99.0,
                         "close": 100.0, "volume": 1e6})
    assert build_window(bars, d) is None
