# Pocket Screener

Screener saham harian **IDX** (Bursa Efek Indonesia) dengan **multi-strategi**
(teknikal & fundamental), prediksi _machine learning_, dan penjelasan otomatis
(_Explainable AI_). Proyek ini adalah **monorepo** dua bagian: frontend Next.js
dan backend FastAPI.

> ⚠️ Proyek edukasi / tugas kuliah. **Bukan nasihat finansial.**

---

## Gambaran Besar

Pocket Screener dibangun dalam tiga fase:

- **Phase 1 — No-Backend.** Semua perhitungan (fetch data Yahoo, indikator teknikal,
  inferensi ML via ONNX Runtime Web) berjalan **sepenuhnya di browser**. Hasil
  backtesting di-_pre-compute_ offline.
- **Phase 2 — Backend.** Seluruh komputasi berat dipindah **server-side** ke
  FastAPI: data pipeline, indikator, inferensi ONNX, screener, composite score,
  AI report, risk meter, support/resistance, market breadth, screener history,
  dan scheduler harian. Frontend kini memanggil **REST API** dan jadi ringan.
- **Phase 3 — Intelligent Multi-Strategy Engine.** Fokus pada **logika** &
  **transparansi**: **9 strategi** (5 teknikal + 4 fundamental) via _Strategy
  Registry_ yang pluggable, data **fundamental** (Yahoo), **Probability Forecast**
  multi-horizon (1D/5D/20D), **Strategy Matrix**, **Strength Score** lintas-strategi,
  serta **Explainable AI** + **Explain Why Selected**.

```
┌─────────────────────────┐         REST/JSON          ┌──────────────────────────┐
│  Frontend (Next.js 16)   │  ───────────────────────►  │  Backend (FastAPI)        │
│  Vercel                  │   /screener[/all], /ranking│  Railway                  │
│                          │   /strategies, /strategy-  │                           │
│  • Dashboard (IHSG)      │     matrix, /strength,     │  • Data pipeline (Yahoo)  │
│  • Screener + panel P3   │   /forecast, /explain,/why,│  • 9 strategi (registry)  │
│  • Strategies (matrix)   │   /fundamentals, /risk,    │  • Composite/AI/Risk/S&R  │
│  • Backtest              │   /stock-report, /history  │  • Forecast 1D/5D/20D (ML)│
└─────────────────────────┘                            │  • APScheduler (WIB)      │
                                                        └────────────┬──────────────┘
                                                                     │
                                       ┌─────────────────────────────┼───────────────┐
                                       ▼                             ▼                ▼
                                 PostgreSQL (Neon)          Redis (Upstash)     ONNX models
                                 market_data, stocks,       cache: harga,       model.onnx +
                                 fundamentals(+derived),    indikator, ranking, forecast_{1,5,20}d
                                 strategy_results,          matrix, report      (RandomForest CPU)
                                 strength_score, forecast,  
                                 screening_history, breadth 
```

---

## Struktur Repo

```
pocket-screener/
├── frontend/   Next.js 16 (App Router) · React 19 · Tailwind v4   → Vercel
├── backend/    FastAPI · SQLAlchemy · ONNX Runtime · APScheduler  → Railway
└── README.md   (file ini)
```

- **Vercel** harus diset **Root Directory = `frontend`**.
- **Backend** men-deploy folder `backend/` ke Railway.
- Database & cache memakai layanan cloud: **Neon** (PostgreSQL) & **Upstash** (Redis).

---

## Fitur Utama

### Phase 2

| Fitur | Endpoint | Keterangan |
| ----- | -------- | ---------- |
| **Screener BSJP & BPJS** | `GET /api/screener` | Dua strategi intraday, kriteria + skor, level Entry/SL/TP, hasil disimpan ke `screening_history`. |
| **Composite Score / Ranking** | `GET /api/ranking` | Skor gabungan 0–100 (Technical 30% · Momentum 25% · Volume 20% · Volatility 10% · ML 15%). |
| **AI Stock Report** | `GET /api/stock-report/{ticker}` | Sentimen Bullish/Bearish, faktor pendukung & risiko, AI Confidence. |
| **Risk Meter** | `GET /api/risk/{ticker}` | Volatilitas, ATR%, Max Drawdown, Beta → Low/Medium/High. |
| **Support & Resistance** | `GET /api/support-resistance/{ticker}` | Swing High/Low, Pivot Point, ATR Band, Breakout Zone. |
| **Market Breadth** | `GET /api/market-breadth` | Naik/turun, Bullish Ratio, Top Gainers/Losers, performa sektor. |
| **Screener History** | `GET /api/history` | Riwayat lolos screener + tracking performa N hari + winrate per strategi. |
| **Market Data** | `GET /api/market-data/{ticker}` | OHLCV + indikator pre-computed (untuk chart). |

### Phase 3 — Multi-Strategy & Explainable

| Fitur | Endpoint | Keterangan |
| ----- | -------- | ---------- |
| **Daftar strategi** | `GET /api/strategies` | Metadata 9 strategi (5 teknikal + 4 fundamental). |
| **Screener 1 strategi** | `GET /api/screener?strategy={name}` | Kandidat 1 strategi + `matched_criteria` (alasan konkret). |
| **Screener semua strategi** | `GET /api/screener/all` | Jalankan 9 strategi sekaligus → tabel `strategy_results`. |
| **Strategy Matrix** | `GET /api/strategy-matrix` | Matriks saham × strategi (lolos / gagal / tak dinilai). |
| **Strength Score** | `GET /api/strength/{ticker}` | Skor kekuatan lintas-strategi 0–100 (bobot configurable). |
| **Probability Forecast** | `GET /api/forecast/{ticker}` | P(return > 0) untuk 1D/5D/20D + confidence + disclaimer. |
| **Explainable AI** | `GET /api/explain/{ticker}` | Confidence + bullish factors + risk factors. |
| **Explain Why Selected** | `GET /api/why/{ticker}` | Strategi yang cocok + alasan per-kriteria yang benar-benar lolos. |
| **Data fundamental** | `GET /api/fundamentals/{ticker}` | Laporan keuangan + metrik turunan (PE/PBV/MarketCap) + growth. |

**9 strategi screening** (via _Strategy Registry_ pluggable):

- **Teknikal:** BSJP · BPJS · Breakout · Trend Following · Potential Reversal
- **Fundamental:** High Growth · Turnaround · Timeless · Cash Rich

**Scheduler harian (WIB / Asia-Jakarta):** 07:00 update data · **07:15 refresh
fundamental** · **07:30 jalankan 9 strategi** · 09:30 & 10:00 & 15:30 screener ·
16:00 ranking · **16:15 forecast** · **16:30 strength score** · 17:00 AI report ·
**Sabtu 06:00 update data fundamental (mingguan)**.

---

## Halaman Frontend

- **Dashboard (`/`)** — konteks pasar **IHSG** (Indeks Harga Saham Gabungan):
  candlestick + AI Report + Risk Meter + Support/Resistance. Simbol terkunci ke IHSG.
- **Screener (`/screener`)** — Market Breadth, tabel screener BSJP/BPJS, chart &
  analitik saham terpilih (AI/Risk/S&R), **Probability Forecast**, **Strength
  Score**, **Explain Panel** (Explainable AI + Why Selected), Composite Score, dan
  Screener History.
- **Strategies (`/strategies`)** — pemilih 9 strategi, hasil per-strategi dengan
  `matched_criteria`, dan **Strategy Comparison Matrix**.
- **Backtest (`/backtest`)** — winrate, cumulative return, drawdown, metrik model.

---

## Menjalankan Secara Lokal

Butuh **Python 3.11** dan **Node.js 20+**.

**1. Backend** (terminal 1)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env               # isi DATABASE_URL (Neon) & REDIS_URL (Upstash)
python -m app.db.init_db             # buat tabel + seed daftar saham
python -m app.core.market_data --range 2y   # ingest OHLCV 2 tahun + indikator
python -m app.data.fundamentals_fetch        # ingest data fundamental (Yahoo)
python -m app.data.fundamentals_derived      # hitung metrik fundamental harian
uvicorn app.main:app --reload --port 8000
```

> **Model forecast** (`forecast_{1,5,20}d.onnx`) sudah disertakan di repo. Untuk
> melatih ulang: `pip install scikit-learn skl2onnx` lalu
> `python -m app.ml.train_forecast` (offline, butuh market_data 2 tahun).

**2. Frontend** (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Buka http://localhost:3000. Frontend membaca `NEXT_PUBLIC_API_BASE_URL`
(default `http://localhost:8000`, jadi jalan tanpa konfigurasi tambahan).

---

## Tech Stack

| Area | Teknologi |
| ---- | --------- |
| Frontend | Next.js 16 (App Router) · React 19 · Tailwind CSS v4 · Lightweight-charts · Recharts |
| Backend | FastAPI · SQLAlchemy 2.0 · APScheduler · httpx |
| Database | PostgreSQL (Neon) |
| Cache | Redis (Upstash) |
| ML | scikit-learn + skl2onnx (training offline) → ONNX → onnxruntime (inferensi server-side) |
| Forecast | 3 model RandomForest terkalibrasi (1D/5D/20D), binary classification P(return > 0) |
| Explainability | Rule-based (`matched_criteria`) + interpretasi fitur teknikal per-saham |
| Deploy | Vercel (frontend) · Railway (backend) |

Detail tiap bagian: **[backend/README.md](backend/README.md)** dan
**[frontend/README.md](frontend/README.md)**.

---

## Kontribusi & Pengembangan

Dikembangkan oleh **Anak Agung Aryadipa Aditya Nugraha**
([@adiityanugraha](https://github.com/adiityanugraha)).

Backend **Phase 2** (data pipeline, composite score, AI report, risk meter,
support/resistance, market breadth, screener history, scheduler) & **Phase 3**
(Strategy Registry 9 strategi, data fundamental, Strategy Matrix, Strength Score,
Probability Forecast, Explainable AI), serta **integrasi frontend ke REST API**,
dikerjakan dengan bantuan **Claude (Anthropic)** sebagai AI pair-programmer
melalui Claude Code — sehingga "Claude" tercatat sebagai _contributor_ pada
riwayat Git repositori ini.

---

## Lisensi

© 2026 Anak Agung Aryadipa Aditya Nugraha. Dirilis di bawah
**[MIT License](LICENSE)** — bebas dipakai/dimodifikasi selama mencantumkan
notice hak cipta & lisensi ini.
