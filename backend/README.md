# Pocket Screener — Backend (Phase 2 + Phase 3)

Backend FastAPI: data pipeline, **9 strategi screening** (5 teknikal + 4
fundamental via _Strategy Registry_), composite score, AI report, risk meter,
support/resistance, market breadth, screener history, **data fundamental**,
**Strategy Matrix**, **Strength Score**, **Probability Forecast** (1D/5D/20D),
**Explainable AI**, dan scheduler harian. Gambaran besar: lihat [../README.md](../README.md).

**Layanan:** PostgreSQL **Neon** · Redis **Upstash** · inferensi ML **ONNX Runtime**
(CPU, server-side) · data OHLCV **&** fundamental dari **Yahoo Finance** (`.JK`;
indeks IHSG → `^JKSE`; fundamental via endpoint `quoteSummary` dengan cookie+crumb).

## Setup lokal (Windows)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # lalu isi DATABASE_URL & REDIS_URL
uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/api/health
- Swagger docs: http://localhost:8000/docs

> Jalankan `uvicorn` via venv. Jika `uvicorn` tak dikenali, aktifkan venv dulu
> (`.\.venv\Scripts\Activate.ps1`) atau pakai `python -m uvicorn ...`.

## Inisialisasi data

```powershell
python -m app.db.init_db              # buat tabel + seed 81 emiten (incl. IHSG)
python -m app.core.market_data --range 2y   # ingest OHLCV 2 tahun + indikator (perlu MA200)
python -m app.data.fundamentals_fetch       # ingest data fundamental (Yahoo quoteSummary)
python -m app.data.fundamentals_derived     # hitung PE/PBV/MarketCap/DividendYield harian
python -m app.db.backfill_screening         # (opsional) isi screening_history historis
```

> Re-ingest **2 tahun** dibutuhkan agar Trend Following (MA200) & forecast punya
> cukup histori. Set `SCHEDULER_ENABLED=false` di `.env` untuk mematikan scheduler
> saat dev/testing.

## Melatih ulang model forecast (offline)

```powershell
pip install scikit-learn skl2onnx     # dependency training (tak perlu saat runtime)
python -m app.ml.train_forecast       # latih 3 model -> forecast_{1,5,20}d.onnx + metrics
```

Fitur = 13 indikator teknikal (jendela 60 bar, sama dgn inferensi). Label =
`close[t+h] > close[t]` untuk h = 1/5/20. Model = `CalibratedClassifierCV`
(RandomForest, sigmoid). Split berbasis tanggal + embargo (cegah kebocoran label).

## Endpoint utama

**Phase 2**

| Endpoint | Fungsi |
| -------- | ------ |
| `GET /api/health` | Status app + database + redis |
| `GET /api/screener` | Screener BSJP & BPJS (+ persist ke `screening_history`) |
| `GET /api/ranking` | Composite Score ranking 0–100 |
| `GET /api/stock-report/{ticker}` | AI Stock Report (sentimen + faktor + confidence) |
| `GET /api/risk/{ticker}` | Risk Meter (volatilitas, ATR, drawdown, beta) |
| `GET /api/support-resistance/{ticker}` | Support/Resistance + Breakout Zone |
| `GET /api/market-breadth` | Breadth pasar (persist harian ke PostgreSQL) |
| `GET /api/history` (`/dates`, `/performance`) | Riwayat screener + tracking + winrate |
| `GET /api/market-data/{ticker}` | OHLCV + indikator (untuk chart) |

**Phase 3**

| Endpoint | Fungsi |
| -------- | ------ |
| `GET /api/strategies` | Daftar 9 strategi (key, nama, tipe, label output) |
| `GET /api/screener?strategy={name}` | Hasil 1 strategi + `matched_criteria` |
| `GET /api/screener/all` | Jalankan 9 strategi → persist `strategy_results` |
| `GET /api/strategy-matrix` | Matriks saham × strategi (lolos/gagal/tak dinilai) |
| `GET /api/strength/{ticker}` | Strength Score 0–100 lintas-strategi (bobot configurable) |
| `GET /api/forecast/{ticker}` | P(return > 0) 1D/5D/20D + confidence + disclaimer |
| `GET /api/explain/{ticker}` | Explainable AI: confidence + bullish/risk factors |
| `GET /api/why/{ticker}` | Strategi cocok + alasan per-kriteria yang lolos |
| `GET /api/fundamentals/{ticker}` | Laporan keuangan + metrik turunan + growth |

**Scheduler (WIB):** 07:00 update data · **07:15 fundamental_derived** · **07:30
9 strategi** · 09:30/10:00/15:30 screener · 16:00 ranking · **16:15 forecast** ·
**16:30 strength** · 17:00 AI report · **Sabtu 06:00 update fundamental (mingguan)**.

**IHSG** disimpan sebagai instrumen indeks (ticker `IHSG` → Yahoo `^JKSE`) dan
**dikecualikan** dari screener/ranking/breadth/strategi — hanya konteks pasar.

## Catatan data fundamental

Sumber gratis (Yahoo) **andal** untuk: revenue & net income tahunan (4 thn),
gross profit (TTM), RoE, kas, total utang, market cap, PE, PBV, dividend yield,
EPS. **Tidak tersedia** untuk IDX: income-from-operations & gross profit per-tahun,
ekuitas/kas per-periode neraca, dan dividend streak — kriteria yang membutuhkannya
(sebagian **Turnaround** & **Timeless**) **dilewati** dan ditandai di
`skipped_criteria`, atau memakai **proxy** berlabel (RoE saat ini ← RoE 5thn;
return histori tersedia ← 10-Year Returns).

## Struktur

```
app/
├── main.py          FastAPI entrypoint (registrasi router)
├── api/             route handlers (screener, ranking, strategies, strategy_matrix,
│                    strength, forecast, explain, why, fundamentals, risk, ...)
├── core/            engine murni (indicators, composite_score, ai_report,
│   ├── strategies/  Strategy Registry: base, registry, 9 file strategi
│   ├── strategy_screener.py · strategy_matrix.py · strength_engine.py
│   └── explain_engine.py · fundamentals.py · risk_meter.py · sr_engine.py · ...
├── data/            pipeline fundamental (fundamentals_fetch, fundamentals_derived)
├── ml/              inferensi ONNX (inference.py, forecast_model.py) + train_forecast.py
│                    + model.onnx, forecast_{1,5,20}d.onnx, *_metrics.json
├── db/              SQLAlchemy models & session
├── cache/           Redis client
└── scheduler/       APScheduler jobs (Phase 2 + Phase 3)
tests/               pytest (regression registry, strategi, fundamental, forecast, scheduler)
```

**Tabel (Phase 2 + Phase 3):** `stocks`, `market_data`, `screening_history`,
`backtesting`, `user_watchlist`, `market_breadth` · **(P3)** `fundamentals`,
`fundamental_derived`, `strategy_results`, `strength_score`, `forecast`.

## Testing

```powershell
python -m pytest tests -q
```

## Keamanan
Kredensial hanya di `.env` (lokal) / environment variables (produksi).
Jangan commit `.env`. Hanya `.env.example` yang di-push.

## Kontribusi
Dikembangkan oleh **Anak Agung Aryadipa Aditya Nugraha**
([@adiityanugraha](https://github.com/adiityanugraha)). Backend Phase 2 & Phase 3
dikerjakan dengan bantuan **Claude (Anthropic)** sebagai AI pair-programmer
melalui Claude Code.
