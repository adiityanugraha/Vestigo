"""Preprocessing input Vestigo-TSFM - salinan SETIA pipeline training.

Model TSFM dilatih di repo terpisah (vestigo-tsfm) di atas lima kanal yang
dihitung src/data/curate.py. Kalau kanal di sini berbeda sedikit saja, ONNX
tetap jalan tanpa error tapi prediksinya memburuk diam-diam. Karena itu modul
ini TIDAK ditulis ulang "dengan gaya sendiri" - urutan dan konstantanya
sengaja identik, dan dikunci oleh tests/test_tsfm_features.py yang
membandingkannya dengan window yang benar-benar dilihat model saat training
(fixture dibuat oleh vestigo-tsfm/scripts/make_vestigo_fixture.py).

Urutan (sama dengan curate.curate_ticker):
  1. harga dipakai apa adanya - Yahoo sudah menyesuaikan split, dividen
     sengaja TIDAK disesuaikan (return = price return)
  2. reindex ke sesi bursa, forward-fill maksimal 3 sesi
  3. bar tidak sah dinolkan SEBELUM return dihitung (volume nol, harga
     non-positif, lompatan melampaui batas ARA/ARB 35 persen)
  4. lima kanal; satu baris berlaku semua-atau-tidak
  5. baris tak sah jadi nol (seperti shard.py), window ditolak bila lebih dari
     MAKS_BARIS_BURUK baris nol

Sesi bursa diturunkan dari data (hari yang punya bar bervolume di >= 30 persen
emiten), bukan dari exchange_calendars. Di training keduanya setara: sesi =
kalender XIDX dikurangi "sesi hantu" berliputan < 30 persen, dan hari di luar
kalender liputannya nol. Versi berbasis data tidak butuh dependensi tambahan
dan otomatis mengenali cuti bersama yang belum dikenal kalender.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CHANNELS = ("log_return", "log_range", "log_volume_z", "close_to_open", "overnight_gap")
CONTEXT = 512
VOL_WINDOW = 60
MAX_FFILL = 3
SANITY_BOUND = 0.35          # batas ARA/ARB IDX
MAKS_BARIS_BURUK = 8         # sama dgn build_finetune.py
PHANTOM_RATIO = 0.30


def trading_sessions(dates_per_ticker: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Sesi = hari dengan bar bervolume di >= 30 persen emiten aktif bulan itu."""
    per_hari: dict = {}
    per_bulan: dict = {}
    for df in dates_per_ticker.values():
        ok = (df["volume"].fillna(0) > 0) & (df["close"].fillna(0) > 0)
        d = pd.DatetimeIndex(pd.to_datetime(df.loc[ok, "date"])).normalize()
        for h in d.unique():
            per_hari[h] = per_hari.get(h, 0) + 1
        for b in d.to_period("M").unique():
            per_bulan[b] = per_bulan.get(b, 0) + 1
    sesi = [h for h, n in per_hari.items() if n >= PHANTOM_RATIO * per_bulan.get(h.to_period("M"), 1)]
    return pd.DatetimeIndex(sorted(sesi))


def _siapkan(bars: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    df = bars.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df = df.drop_duplicates(subset="date").set_index("date").sort_index()
    for k in ("open", "high", "low", "close"):
        df[f"adj_{k}"] = df[k].astype(float)
    df["adj_volume"] = df["volume"].astype(float)

    sesi = sessions[(sessions >= df.index.min()) & (sessions <= df.index.max())]
    df = df.reindex(sesi)
    kolom = [c for c in df.columns if c.startswith("adj_") or c in ("open", "high", "low", "close", "volume")]
    df[kolom] = df[kolom].ffill(limit=MAX_FFILL)
    return df


def _mask_invalid_bars(df: pd.DataFrame) -> pd.DataFrame:
    price_cols = ["adj_open", "adj_high", "adj_low", "adj_close"]
    df = df.copy()
    invalid = (df[price_cols] <= 0).any(axis=1)
    if (df["adj_volume"].fillna(0) > 0).any():
        invalid = invalid | (df["adj_volume"].fillna(0) <= 0)
    df.loc[invalid, price_cols + ["adj_volume"]] = np.nan

    rng = np.log(df["adj_high"] / df["adj_low"])
    ret = np.log(df["adj_close"] / df["adj_close"].shift(1))
    rusak = (rng.abs() > SANITY_BOUND) | (ret.abs() > SANITY_BOUND)
    df.loc[rusak.fillna(False), price_cols + ["adj_volume"]] = np.nan
    return df


def compute_channels(bars: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Lima kanal per sesi, persis seperti curate.compute_channels."""
    df = _mask_invalid_bars(_siapkan(bars, sessions))
    out = pd.DataFrame(index=df.index)
    out["log_return"] = np.log(df["adj_close"] / df["adj_close"].shift(1))
    out["log_range"] = np.log(df["adj_high"] / df["adj_low"])
    out["close_to_open"] = np.log(df["adj_close"] / df["adj_open"])
    out["overnight_gap"] = np.log(df["adj_open"] / df["adj_close"].shift(1))
    lv = np.log1p(df["adj_volume"])
    roll = lv.rolling(VOL_WINDOW, min_periods=20)
    out["log_volume_z"] = (lv - roll.mean()) / (roll.std() + 1e-8)
    out = out[list(CHANNELS)].replace([np.inf, -np.inf], np.nan)
    out.loc[out.isna().any(axis=1)] = np.nan
    return out


def build_window(bars: pd.DataFrame, sessions: pd.DatetimeIndex,
                 as_of: pd.Timestamp | None = None) -> tuple[np.ndarray, int] | None:
    """Window (5, 512) float32 untuk ONNX, berakhir di `as_of` (default sesi terakhir).

    Mengembalikan (window, n_baris_buruk), atau None bila riwayat kurang atau
    baris buruknya melebihi toleransi training.
    """
    ch = compute_channels(bars, sessions)
    if as_of is not None:
        ch = ch[ch.index <= pd.Timestamp(as_of)]
    if len(ch) < CONTEXT:
        return None
    w = ch.iloc[-CONTEXT:]
    buruk = int(w.isna().any(axis=1).sum())
    if buruk > MAKS_BARIS_BURUK:
        return None
    return np.nan_to_num(w.to_numpy(np.float32), nan=0.0).T.copy(), buruk
