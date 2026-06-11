"""Training Probability Forecast multi-horizon (Phase 3 Day 11, OFFLINE).

Melatih 3 classifier biner terkalibrasi (horizon 1D / 5D / 20D) yang
memprediksi P(return > 0) setelah N hari. Output:
  - forecast_1d.onnx, forecast_5d.onnx, forecast_20d.onnx
  - forecast_metrics.json (akurasi, AUC, Brier, kalibrasi, backtest, threshold
    confidence, feature columns)

Prinsip penting:
  - FITUR = 13 fitur teknikal (app.ml.features.build_feature_vector), DIBANGUN
    DARI JENDELA 60 BAR (sama dgn LOOKBACK_BARS inference) -> distribusi fitur
    saat training IDENTIK dengan saat prediksi. Fundamental TIDAK dipakai (tak
    ada histori point-in-time -> akan jadi lookahead bias).
  - LABEL  = apakah close[i+h] > close[i].
  - SPLIT  = berdasarkan tanggal (train lampau, test masa depan) + embargo 30
    hari agar label train tidak bocor ke periode test.
  - KALIBRASI = CalibratedClassifierCV (sigmoid/Platt) -> probabilitas jujur.

Jalankan (venv aktif, butuh scikit-learn + skl2onnx):
    python -m app.ml.train_forecast
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.core.instruments import is_index
from app.ml.features import MODEL_FEATURE_COLUMNS, build_feature_vector
from app.ml.inference import LOOKBACK_BARS

HORIZONS = (1, 5, 20)
ML_DIR = Path(__file__).resolve().parent
TEST_FRACTION = 0.20      # 20% tanggal terakhir jadi test
EMBARGO_DAYS = 30         # gap kalender antara train & test (cegah kebocoran label)
RANDOM_STATE = 42

# Ambang confidence dari jarak |p - 0.5| (dipakai Day 12).
CONFIDENCE_THRESHOLDS = {"medium": 0.07, "high": 0.18}


def load_bars_by_ticker() -> dict[str, list]:
    from app.db.models import MarketData
    from app.db.session import SessionLocal

    if SessionLocal is None:
        raise SystemExit("DATABASE_URL belum diset di backend/.env")

    from sqlalchemy import select

    db = SessionLocal()
    try:
        rows = db.scalars(select(MarketData).order_by(MarketData.ticker, MarketData.date))
        grouped: dict[str, list] = {}
        for row in rows:
            if is_index(row.ticker):
                continue
            grouped.setdefault(row.ticker, []).append(row)
        return grouped
    finally:
        db.close()


def build_dataset(bars_by_ticker: dict[str, list]) -> pd.DataFrame:
    """Rakit sampel (fitur jendela-60 + label/return tiap horizon + tanggal)."""
    records: list[dict] = []
    max_h = max(HORIZONS)

    for ticker, bars in bars_by_ticker.items():
        closes = [float(b.close) for b in bars]
        n = len(bars)
        # i butuh >= LOOKBACK-1 bar ke belakang & max_h bar ke depan.
        for i in range(LOOKBACK_BARS - 1, n - max_h):
            window = bars[i - LOOKBACK_BARS + 1 : i + 1]
            features = build_feature_vector(window)
            if features is None:
                continue
            cur = closes[i]
            if cur <= 0:
                continue
            record = {"date": bars[i].date, "ticker": ticker}
            for j, col in enumerate(MODEL_FEATURE_COLUMNS):
                record[col] = features[j]
            for h in HORIZONS:
                fut = closes[i + h]
                record[f"y{h}"] = int(fut > cur)
                record[f"r{h}"] = fut / cur - 1
            records.append(record)

    df = pd.DataFrame.from_records(records)
    return df.sort_values("date").reset_index(drop=True)


def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Split berdasarkan tanggal + embargo agar label train tak bocor ke test."""
    dates = df["date"]
    split_date = dates.quantile(1 - TEST_FRACTION)
    embargo = split_date - timedelta(days=EMBARGO_DAYS)
    train = df[df["date"] < embargo].copy()
    test = df[df["date"] >= split_date].copy()
    return train, test, str(split_date)


def calibration_bins(y_true: np.ndarray, proba: np.ndarray, n_bins: int = 10) -> list[dict]:
    """Kurva kalibrasi: rata-rata prediksi vs frekuensi aktual per bin."""
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(proba, bins) - 1, 0, n_bins - 1)
    out: list[dict] = []
    for b in range(n_bins):
        mask = idx == b
        if mask.sum() == 0:
            continue
        out.append(
            {
                "bin": f"{bins[b]:.1f}-{bins[b + 1]:.1f}",
                "count": int(mask.sum()),
                "mean_pred": round(float(proba[mask].mean()), 4),
                "actual_rate": round(float(y_true[mask].mean()), 4),
            }
        )
    return out


def backtest_by_tercile(proba: np.ndarray, forward_return: np.ndarray) -> list[dict]:
    """Rata-rata return ke depan per tercile probabilitas (sanity ekonomi)."""
    order = np.argsort(proba)
    thirds = np.array_split(order, 3)
    labels = ["low_prob", "mid_prob", "high_prob"]
    out: list[dict] = []
    for label, group in zip(labels, thirds):
        out.append(
            {
                "tercile": label,
                "count": int(len(group)),
                "mean_pred": round(float(proba[group].mean()), 4),
                "mean_forward_return_pct": round(float(forward_return[group].mean() * 100), 3),
                "win_rate": round(float((forward_return[group] > 0).mean()), 4),
            }
        )
    return out


def train_horizon(
    horizon: int, x_train, y_train, x_test, y_test, ret_test
) -> tuple[CalibratedClassifierCV, dict]:
    base = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=50,   # regularisasi kuat: sinyal finansial sangat noisy
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    model = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    model.fit(x_train, y_train)

    proba = model.predict_proba(x_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "horizon_days": horizon,
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "base_rate_test": round(float(np.mean(y_test)), 4),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "brier": round(float(brier_score_loss(y_test, proba)), 4),
        "calibration": calibration_bins(y_test, proba),
        "backtest_terciles": backtest_by_tercile(proba, ret_test),
    }
    return model, metrics


def export_onnx(model: CalibratedClassifierCV, path: Path) -> None:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType

    initial_type = [("float_input", FloatTensorType([None, len(MODEL_FEATURE_COLUMNS)]))]
    onx = convert_sklearn(
        model,
        initial_types=initial_type,
        options={id(model): {"zipmap": False}},  # probabilities sbg tensor [N,2]
        target_opset=18,
    )
    path.write_bytes(onx.SerializeToString())


def main() -> None:
    print("Memuat bar dari market_data...")
    bars_by_ticker = load_bars_by_ticker()
    print(f"  {len(bars_by_ticker)} ticker (indeks dikecualikan).")

    print("Membangun dataset (fitur jendela-60 + label 1D/5D/20D)...")
    df = build_dataset(bars_by_ticker)
    print(f"  {len(df):,} sampel, rentang {df['date'].min()} .. {df['date'].max()}")

    train_df, test_df, split_date = time_split(df)
    print(f"  split_date={split_date}  train={len(train_df):,}  test={len(test_df):,}")

    feature_cols = list(MODEL_FEATURE_COLUMNS)
    x_train = train_df[feature_cols].to_numpy(dtype=np.float32)
    x_test = test_df[feature_cols].to_numpy(dtype=np.float32)

    all_metrics: dict = {
        "model": "CalibratedClassifierCV(RandomForest, sigmoid)",
        "target": "P(close[t+h] > close[t])",
        "features": feature_cols,
        "lookback_bars": LOOKBACK_BARS,
        "horizons": list(HORIZONS),
        "split_date": split_date,
        "embargo_days": EMBARGO_DAYS,
        "confidence_thresholds": CONFIDENCE_THRESHOLDS,
        "per_horizon": {},
    }

    for h in HORIZONS:
        print(f"\nMelatih horizon {h}D...")
        y_train = train_df[f"y{h}"].to_numpy()
        y_test = test_df[f"y{h}"].to_numpy()
        ret_test = test_df[f"r{h}"].to_numpy()
        model, metrics = train_horizon(h, x_train, y_train, x_test, y_test, ret_test)
        all_metrics["per_horizon"][f"{h}d"] = metrics
        print(
            f"  acc={metrics['accuracy']} auc={metrics['roc_auc']} "
            f"brier={metrics['brier']} base_rate={metrics['base_rate_test']}"
        )

        out_path = ML_DIR / f"forecast_{h}d.onnx"
        export_onnx(model, out_path)
        print(f"  -> {out_path.name} ({out_path.stat().st_size // 1024} KB)")

    metrics_path = ML_DIR / "forecast_metrics.json"
    metrics_path.write_text(json.dumps(all_metrics, indent=2))
    print(f"\nMetrics ditulis ke {metrics_path.name}. Selesai.")


if __name__ == "__main__":
    main()
