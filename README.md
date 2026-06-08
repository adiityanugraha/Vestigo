# Pocket Screener

Screener saham harian **IDX** (Bursa Efek Indonesia) dengan prediksi _machine
learning_, analitik teknikal, dan laporan otomatis. Proyek ini adalah **monorepo**
dua bagian: frontend Next.js dan backend FastAPI.

> ⚠️ Proyek edukasi / tugas kuliah. **Bukan nasihat finansial.**

---

## Gambaran Besar

Pocket Screener dibangun dalam dua fase:

- **Phase 1 — No-Backend.** Semua perhitungan (fetch data Yahoo, indikator teknikal,
  inferensi ML via ONNX Runtime Web) berjalan **sepenuhnya di browser**. Hasil
  backtesting di-_pre-compute_ offline.
- **Phase 2 — Backend.** Seluruh komputasi berat dipindah **server-side** ke
  FastAPI: data pipeline, indikator, inferensi ONNX, screener, composite score,
  AI report, risk meter, support/resistance, market breadth, screener history,
  dan scheduler harian. Frontend kini memanggil **REST API** dan jadi ringan.

```
┌─────────────────────────┐         REST/JSON          ┌──────────────────────────┐
│  Frontend (Next.js 16)   │  ───────────────────────►  │  Backend (FastAPI)        │
│  Vercel                  │   /api/screener, /ranking, │  Railway                  │
│                          │   /stock-report, /risk,    │                           │
│  • Dashboard (IHSG)      │   /support-resistance,     │  • Data pipeline (Yahoo)  │
│  • Screener              │   /market-breadth,         │  • Indicators + ONNX ML   │
│  • Backtest              │   /history, /market-data   │  • Composite/AI/Risk/S&R  │
└─────────────────────────┘                            │  • APScheduler (WIB)      │
                                                        └────────────┬──────────────┘
                                                                     │
                                       ┌─────────────────────────────┼───────────────┐
                                       ▼                             ▼                ▼
                                 PostgreSQL (Neon)          Redis (Upstash)     model.onnx
                                 market_data, stocks,       cache: harga,       (RandomForest,
                                 screening_history,         indikator, ranking, inferensi CPU)
                                 backtesting, breadth       report, S&R
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

**Scheduler harian (WIB / Asia-Jakarta):** 07:00 update data · 09:30 & 10:00 & 15:30 screener · 16:00 ranking · 17:00 AI report.

---

## Halaman Frontend

- **Dashboard (`/`)** — konteks pasar **IHSG** (Indeks Harga Saham Gabungan):
  candlestick + AI Report + Risk Meter + Support/Resistance. Simbol terkunci ke IHSG.
- **Screener (`/screener`)** — Market Breadth, tabel screener BSJP/BPJS, chart &
  analitik saham terpilih (AI/Risk/S&R), Composite Score, dan Screener History.
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
copy .env.example .env          # isi DATABASE_URL (Neon) & REDIS_URL (Upstash)
python -m app.db.init_db        # buat tabel + seed daftar saham
python -m app.core.market_data  # ingest OHLCV + indikator
uvicorn app.main:app --reload --port 8000
```

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
| ML | scikit-learn (training offline) → ONNX → onnxruntime (inferensi server-side) |
| Deploy | Vercel (frontend) · Railway (backend) |

Detail tiap bagian: **[backend/README.md](backend/README.md)** dan
**[frontend/README.md](frontend/README.md)**.

---

## Kontribusi & Pengembangan

Dikembangkan oleh **[@adiityanugraha](https://github.com/adiityanugraha)**.

Backend **Phase 2** (FastAPI: data pipeline, composite score, AI report, risk
meter, support/resistance, market breadth, screener history, scheduler) dan
**integrasi frontend ke REST API** dikerjakan dengan bantuan **Claude
(Anthropic)** sebagai AI pair-programmer melalui Claude Code — sehingga
"Claude" tercatat sebagai _contributor_ pada riwayat Git repositori ini.
