"""Inferensi harian Vestigo-TSFM (Phase 6, M8).

Model: transformer time-series ~34 juta parameter, dilatih di repo vestigo-tsfm
(pretraining 3 miliar token multi-pasar, fine-tune IDX, walk-forward 10 fold,
holdout 2025-2026). Diekspor ke ONNX dengan paritas torch vs onnx 2,4e-6.

DUA ATURAN yang dijaga di sini, keduanya dari masalah nyata:

1. BAR HARI INI TIDAK PERNAH DIPAKAI. market_data diperbarui lewat upsert, dan
   fetch yang jalan di jam bursa menyimpan bar setengah jadi (terverifikasi:
   BBCA 2026-07-10 tercatat volume 68,5 juta, versi final 138 juta). Satu bar
   itu membuat kanal volume meleset 1,1. Karena itu input selalu berakhir di
   sesi terakhir yang tanggalnya SEBELUM hari ini (WIB).

2. PREPROCESSING IDENTIK dengan training - lihat app.ml.tsfm_features dan
   tests/test_tsfm_features.py. Diverifikasi di data produksi: 77 dari 77
   emiten memberi window yang sama persis (selisih 0) dengan training.

Cara memakai keluarannya, sesuai temuan riset (lihat /api/tsfm/model-card):
`rank_score` adalah satu-satunya keluaran dengan sinyal peringkat yang teruji
(IC walk-forward 0,050). Probabilitas arah terbukti hanya proxy volatilitas.
Setelah biaya transaksi IDX, strategi long-only di atasnya tidak mengalahkan
beli-tahan IHSG di 2016-2024. Ini alat riset, bukan sinyal beli.
"""

from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.instruments import is_index
from app.db.models import MarketData
from app.ml.tsfm_features import build_window, trading_sessions

log = logging.getLogger("ml.tsfm")

_DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "tsfm.onnx"
MODEL_VERSION = "tsfm-30m-stageD-s2500"
HORIZON = 10
REGIME = ("trending_up", "trending_down", "ranging", "high_vol")
WIB = timezone(timedelta(hours=7))
# Data yang sesi terakhirnya lebih tua dari ini = pipeline market data mati.
# 7 hari kalender menampung akhir pekan + libur biasa; setelah cuti panjang
# (Lebaran) job melewatkan satu hari, dan itu tidak merugikan karena memang
# tidak ada sesi baru untuk diprediksi.
MAKS_UMUR_DATA_HARI = 7

_session: ort.InferenceSession | None = None
_lock = threading.Lock()


def _model_path() -> Path:
    override = get_settings().tsfm_model_path
    return Path(override) if override else _DEFAULT_MODEL_PATH


def model_tersedia() -> bool:
    return _model_path().exists()


def get_session() -> ort.InferenceSession:
    global _session
    if _session is not None:
        return _session
    with _lock:
        if _session is None:
            path = _model_path()
            if not path.exists():
                raise FileNotFoundError(
                    f"Model TSFM tidak ditemukan: {path}. Salin dari "
                    "vestigo-tsfm/artifacts/tsfm.onnx atau set TSFM_MODEL_PATH."
                )
            _session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    return _session


def hari_ini_wib() -> date:
    return datetime.now(WIB).date()


def load_bars(db: Session, tickers: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """OHLCV per emiten. Semua emiten diperlukan untuk menurunkan sesi bursa."""
    q = select(MarketData.ticker, MarketData.date, MarketData.open, MarketData.high,
               MarketData.low, MarketData.close, MarketData.volume)
    if tickers:
        q = q.where(MarketData.ticker.in_(tickers))
    df = pd.DataFrame(db.execute(q).all(),
                      columns=["ticker", "date", "open", "high", "low", "close", "volume"])
    return {t: g.drop(columns="ticker").reset_index(drop=True)
            for t, g in df.groupby("ticker") if not is_index(t)}


def sesi_final(bars: dict[str, pd.DataFrame], hari_ini: date | None = None) -> pd.DatetimeIndex:
    """Sesi bursa yang sudah final: tanggal < hari ini (WIB)."""
    batas = pd.Timestamp(hari_ini or hari_ini_wib())
    sesi = trading_sessions(bars)
    return sesi[sesi < batas]


def batas_live(as_of: pd.Timestamp) -> datetime:
    """Batas waktu agar prediksi untuk `as_of` masih berstatus live.

    Posisi dieksekusi di open sesi BERIKUTNYA (09:00 WIB). Prediksi yang dibuat
    setelah itu sudah bisa "melihat" sebagian horizonnya. Kalender bursa ke depan
    tidak diketahui, jadi sesi berikutnya diasumsikan hari kerja pertama setelah
    `as_of`. Kalau hari itu ternyata libur, prediksi yang sebenarnya masih live
    ikut ditandai susulan - salahnya ke arah yang aman, tidak sebaliknya.
    """
    d = pd.Timestamp(as_of).normalize() + pd.Timedelta(days=1)
    while d.weekday() >= 5:
        d += pd.Timedelta(days=1)
    return datetime(d.year, d.month, d.day, 9, 0, tzinfo=WIB)


def data_basi(sessions: pd.DatetimeIndex, hari_ini: date | None = None) -> int | None:
    """Umur sesi final terakhir (hari) bila melewati batas, None bila segar.

    Kasus nyata yang memicu aturan ini: scheduler berhenti sejak 2026-07-10
    setelah fetch manual di jam bursa menyimpan bar setengah jadi. Tanpa
    pengaman, job 2,5 bulan kemudian tetap "berhasil" dan menulis prediksi dari
    bar cacat itu. Dalam operasi normal bar setengah jadi tidak bisa lolos
    (fetch 07:00 menimpanya), jadi yang perlu dideteksi adalah pipeline mati.
    """
    if len(sessions) == 0:
        return None
    umur = (pd.Timestamp(hari_ini or hari_ini_wib()) - sessions[-1]).days
    return umur if umur > MAKS_UMUR_DATA_HARI else None


def predict_all(bars: dict[str, pd.DataFrame], sessions: pd.DatetimeIndex,
                as_of: pd.Timestamp | None = None) -> tuple[pd.Timestamp, list[dict]]:
    """Prediksi seluruh emiten per `as_of` (default sesi final terakhir)."""
    as_of = pd.Timestamp(as_of) if as_of is not None else sessions[-1]
    nama, window, buruk = [], [], []
    for tk, b in bars.items():
        b = b[pd.to_datetime(b["date"]) <= as_of]
        if b.empty or pd.Timestamp(b["date"].max()) < as_of:
            continue                                   # emiten tanpa bar di sesi as_of
        hasil = build_window(b, sessions[sessions <= as_of], as_of=as_of)
        if hasil is None:
            continue
        nama.append(tk)
        window.append(hasil[0])
        buruk.append(hasil[1])
    if not nama:
        return as_of, []

    sess = get_session()
    p_arah, log_vol, p_regime, skor = sess.run(None, {"window": np.stack(window).astype(np.float32)})
    urut = skor.argsort().argsort()
    pct = urut / max(1, len(skor) - 1)
    return as_of, [{
        "ticker": tk, "rank_score": float(skor[i]), "rank_pct": float(pct[i]),
        "prob_down": float(p_arah[i, 0]), "prob_flat": float(p_arah[i, 1]), "prob_up": float(p_arah[i, 2]),
        "predicted_vol": float(np.exp(log_vol[i])),
        "regime": REGIME[int(p_regime[i].argmax())], "regime_prob": float(p_regime[i].max()),
        "bad_rows": int(buruk[i]),
    } for i, tk in enumerate(nama)]


def realisasi(bars: pd.DataFrame, sessions: pd.DatetimeIndex, pred_date: pd.Timestamp,
              horizon: int = HORIZON) -> tuple[float, float] | None:
    """(log return close t -> t+H, std log return harian t+1..t+H) atau None bila belum lewat H sesi final."""
    sesi = sessions[sessions >= pd.Timestamp(pred_date)]
    if len(sesi) <= horizon:
        return None
    b = bars.assign(date=pd.to_datetime(bars["date"])).set_index("date")
    jalur = b.reindex(sesi[: horizon + 1])
    c = jalur["close"].astype(float)
    # sama dengan label training: bar tanpa transaksi di jalur -> label tidak sah
    if c.isna().any() or (c <= 0).any() or (jalur["volume"].fillna(0) <= 0).any():
        return None
    r = np.diff(np.log(c.to_numpy()))
    return float(r.sum()), float(r.std())
